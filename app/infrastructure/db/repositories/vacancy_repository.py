from datetime import datetime

from sqlalchemy import Select, distinct, func, select, true, update
from sqlalchemy.dialects.postgresql import array
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.selectable import TableValuedAlias

from app.domain.vacancy.entities import DispatchedVacancy, DispatchMatch, Vacancy
from app.domain.vacancy.market import MarketAggregates, SalarySample
from app.domain.vacancy.repository import IVacancyRepository
from app.domain.vacancy.value_objects import ContentHash, VacancyId
from app.infrastructure.db.mappers.vacancy import (
    apply_vacancy,
    vacancy_for_stats,
    vacancy_from_model,
    vacancy_to_model,
)
from app.infrastructure.db.models import Vacancy as VacancyModel
from app.infrastructure.db.models import VacancyDispatchLog

# Отметка «не подходит» в vacancy_dispatch_log.feedback.
FEEDBACK_REJECTED = "rejected"


def _json_elements(column: InstrumentedAttribute[list[str]], name: str) -> TableValuedAlias:
    """Разворачивает JSONB-список в строки: одна вакансия — несколько направлений."""
    return func.jsonb_array_elements_text(column).table_valued("value").render_derived(name=name)


def _salary_sample(median: float | None, sample: int) -> SalarySample:
    return SalarySample(round(median) if median is not None else None, int(sample))


class VacancyRepository(IVacancyRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, vacancy_id: VacancyId) -> Vacancy | None:
        result = await self._session.execute(
            select(VacancyModel).where(VacancyModel.id == vacancy_id.value)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return vacancy_from_model(model)

    async def find_for_profile_since(
        self,
        specializations: set[str],
        skills: set[str],
        since: datetime,
    ) -> list[Vacancy]:
        """Зеркало SQL-префильтра из UserRepository.find_prefiltered_candidates.

        Там по вакансии ищут юзеров, здесь по профилю юзера — вакансии.
        Пустой профиль не матчится ни с чем: у вакансии всегда есть
        специализация и скиллы, поэтому пересечения не будет.
        """
        if not specializations or not skills:
            return []

        # Колонки поимённо, без text: ни воронке, ни тренду, ни разбивке по
        # компаниям он не нужен, а весит в среднем 1296 символов при выборке
        # до тысячи строк. Замер на проде: 21.5 мс против 8.1.
        # Кортежи, а не сущности ORM: с отложенной колонкой любое обращение к
        # ней обернулось бы отдельным запросом на каждую строку.
        query = (
            select(
                VacancyModel.id,
                VacancyModel.specializations,
                VacancyModel.skills,
                VacancyModel.grade,
                VacancyModel.experience_level,
                VacancyModel.work_format,
                VacancyModel.company_type,
                VacancyModel.salary_amount,
                VacancyModel.salary_currency,
                VacancyModel.created_at,
            )
            .where(VacancyModel.is_active.is_(True))
            .where(VacancyModel.created_at >= since)
            .where(VacancyModel.specializations.bool_op("?|")(array(sorted(specializations))))
            .where(VacancyModel.skills.bool_op("?|")(array(sorted(skills))))
        )
        result = await self._session.execute(query)
        return [vacancy_for_stats(row) for row in result.all()]

    async def find_for_specializations_since(
        self,
        specializations: set[str],
        since: datetime,
    ) -> list[Vacancy]:
        """Всё по специализациям пользователя, без учёта навыков.

        Нужно, чтобы показать потерю на префильтре: воронка начинается уже
        после него и эту часть не видит. Окно короче, чем у трендов, — иначе
        строк набирается слишком много.
        """
        if not specializations:
            return []

        query = (
            select(
                VacancyModel.id,
                VacancyModel.specializations,
                VacancyModel.skills,
                VacancyModel.grade,
                VacancyModel.experience_level,
                VacancyModel.work_format,
                VacancyModel.company_type,
                VacancyModel.salary_amount,
                VacancyModel.salary_currency,
                VacancyModel.created_at,
            )
            .where(VacancyModel.is_active.is_(True))
            .where(VacancyModel.created_at >= since)
            .where(VacancyModel.specializations.bool_op("?|")(array(sorted(specializations))))
        )
        result = await self._session.execute(query)
        return [vacancy_for_stats(row) for row in result.all()]

    async def find_dispatched_for_user(
        self, user_tg_id: int, limit: int | None = None
    ) -> list[DispatchedVacancy]:
        query = (
            select(VacancyModel, VacancyDispatchLog.dispatched_at)
            .join(VacancyDispatchLog, VacancyDispatchLog.vacancy_id == VacancyModel.id)
            .where(VacancyDispatchLog.user_tg_id == user_tg_id)
            .order_by(VacancyDispatchLog.dispatched_at.desc())
        )
        if limit is not None:
            query = query.limit(limit)
        result = await self._session.execute(query)
        return [
            DispatchedVacancy(vacancy=vacancy_from_model(model), dispatched_at=dispatched_at)
            for model, dispatched_at in result.all()
        ]

    async def count_dispatched_for_user(self, user_tg_id: int) -> tuple[int, datetime | None]:
        query = select(
            func.count(VacancyDispatchLog.id),
            func.min(VacancyDispatchLog.dispatched_at),
        ).where(VacancyDispatchLog.user_tg_id == user_tg_id)
        count, since = (await self._session.execute(query)).one()
        return int(count), since

    async def count_dispatches_between(
        self, user_tg_id: int, since: datetime, until: datetime
    ) -> tuple[int, int]:
        """Сколько вакансий ушло человеку за окно и сколько он отметил «не подходит»."""
        query = select(
            func.count(VacancyDispatchLog.id),
            func.count(VacancyDispatchLog.id).filter(
                VacancyDispatchLog.feedback == FEEDBACK_REJECTED
            ),
        ).where(
            VacancyDispatchLog.user_tg_id == user_tg_id,
            VacancyDispatchLog.dispatched_at >= since,
            VacancyDispatchLog.dispatched_at < until,
        )
        sent, rejected = (await self._session.execute(query)).one()
        return int(sent), int(rejected)

    async def get_dispatch_match(
        self, vacancy_id: VacancyId, user_tg_id: int
    ) -> DispatchMatch | None:
        row = (
            await self._session.execute(
                select(
                    VacancyDispatchLog.matched_specializations,
                    VacancyDispatchLog.matched_skills,
                )
                .where(VacancyDispatchLog.vacancy_id == vacancy_id.value)
                .where(VacancyDispatchLog.user_tg_id == user_tg_id)
            )
        ).first()
        if row is None:
            return None
        # У отправок до снимка специализаций их нет.
        return DispatchMatch(
            matched_specializations=row.matched_specializations or [],
            matched_skills=row.matched_skills or [],
        )

    async def reject_dispatch(self, vacancy_id: VacancyId, user_tg_id: int, at: datetime) -> None:
        await self._set_feedback(vacancy_id, user_tg_id, FEEDBACK_REJECTED, at)

    async def clear_dispatch_feedback(self, vacancy_id: VacancyId, user_tg_id: int) -> None:
        await self._set_feedback(vacancy_id, user_tg_id, None, None)

    async def _set_feedback(
        self,
        vacancy_id: VacancyId,
        user_tg_id: int,
        feedback: str | None,
        at: datetime | None,
    ) -> None:
        await self._session.execute(
            update(VacancyDispatchLog)
            .where(VacancyDispatchLog.vacancy_id == vacancy_id.value)
            .where(VacancyDispatchLog.user_tg_id == user_tg_id)
            .values(feedback=feedback, feedback_at=at)
        )

    async def salary_median(
        self,
        specialization: str,
        grade: str | None,
        since: datetime,
        until: datetime,
    ) -> tuple[int | None, int]:
        """Медиана зарплаты и число вакансий, по которым она посчитана.

        Число нужно вызывающему: медиана по трём вакансиям — не рынок.
        """
        query = (
            select(
                func.percentile_cont(0.5).within_group(VacancyModel.salary_amount),
                func.count(VacancyModel.salary_amount),
            )
            .where(VacancyModel.created_at >= since)
            .where(VacancyModel.created_at < until)
            .where(VacancyModel.salary_amount.is_not(None))
            .where(VacancyModel.specializations.contains([specialization]))
        )
        if grade is not None:
            query = query.where(VacancyModel.grade == grade)
        median, sample = (await self._session.execute(query)).one()
        return (round(median) if median is not None else None), int(sample)

    async def market_aggregates(
        self, counts_since: datetime, salary_since: datetime
    ) -> MarketAggregates:
        vacancies, with_salary, channels = (
            await self._session.execute(
                select(
                    func.count(),
                    func.count(VacancyModel.salary_amount),
                    func.count(distinct(VacancyModel.source_channel)),
                ).where(VacancyModel.created_at >= counts_since)
            )
        ).one()
        all_time = (await self._session.execute(select(func.count(VacancyModel.id)))).scalar_one()

        spec = _json_elements(VacancyModel.specializations, "spec")
        skill = _json_elements(VacancyModel.skills, "skill")
        median = func.percentile_cont(0.5).within_group(VacancyModel.salary_amount)

        by_specialization = await self._counts(
            select(spec.c.value, func.count())
            .select_from(VacancyModel)
            .join(spec, true())
            .where(VacancyModel.created_at >= counts_since)
            .group_by(spec.c.value)
        )
        by_skill = await self._counts(
            select(skill.c.value, func.count())
            .select_from(VacancyModel)
            .join(skill, true())
            .where(VacancyModel.created_at >= counts_since)
            .group_by(skill.c.value)
        )
        by_work_format = await self._counts(
            select(VacancyModel.work_format, func.count())
            .where(VacancyModel.created_at >= counts_since)
            .group_by(VacancyModel.work_format)
        )

        salary_rows = await self._session.execute(
            select(spec.c.value, median, func.count())
            .select_from(VacancyModel)
            .join(spec, true())
            .where(VacancyModel.created_at >= salary_since)
            .where(VacancyModel.salary_amount.is_not(None))
            .group_by(spec.c.value)
        )
        salary_grade_rows = await self._session.execute(
            select(spec.c.value, VacancyModel.grade, median, func.count())
            .select_from(VacancyModel)
            .join(spec, true())
            .where(VacancyModel.created_at >= salary_since)
            .where(VacancyModel.salary_amount.is_not(None))
            .group_by(spec.c.value, VacancyModel.grade)
        )

        return MarketAggregates(
            vacancies=int(vacancies),
            with_salary=int(with_salary),
            channels=int(channels),
            by_specialization=by_specialization,
            by_work_format=by_work_format,
            by_skill=by_skill,
            salary_by_specialization={
                name: _salary_sample(value, sample) for name, value, sample in salary_rows
            },
            salary_by_specialization_grade={
                (name, grade): _salary_sample(value, sample)
                for name, grade, value, sample in salary_grade_rows
            },
            all_time=int(all_time),
        )

    async def _counts(self, query: Select[tuple[str, int]]) -> dict[str, int]:
        rows = await self._session.execute(query)
        return {str(key): int(count) for key, count in rows}

    async def exists_by_content_hash(self, content_hash: ContentHash) -> bool:
        result = await self._session.execute(
            select(VacancyModel.id).where(VacancyModel.content_hash == content_hash.value)
        )
        return result.scalar_one_or_none() is not None

    async def add(self, vacancy: Vacancy) -> None:
        self._session.add(vacancy_to_model(vacancy))

    async def update(self, vacancy: Vacancy) -> None:
        result = await self._session.execute(
            select(VacancyModel).where(VacancyModel.id == vacancy.id.value)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError("Vacancy not found")
        apply_vacancy(model, vacancy)

    async def upsert(self, vacancy: Vacancy) -> None:
        result = await self._session.execute(
            select(VacancyModel).where(VacancyModel.content_hash == vacancy.content_hash.value)
        )
        model = result.scalar_one_or_none()
        if model is None:
            self._session.add(vacancy_to_model(vacancy))
            return
        apply_vacancy(model, vacancy)
