from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import array
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.vacancy.entities import DispatchedVacancy, Vacancy
from app.domain.vacancy.repository import IVacancyRepository
from app.domain.vacancy.value_objects import ContentHash, VacancyId
from app.infrastructure.db.mappers.vacancy import (
    apply_vacancy,
    vacancy_from_model,
    vacancy_to_model,
)
from app.infrastructure.db.models import Vacancy as VacancyModel
from app.infrastructure.db.models import VacancyDispatchLog


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

        query = (
            select(VacancyModel)
            .where(VacancyModel.is_active.is_(True))
            .where(VacancyModel.created_at >= since)
            .where(VacancyModel.specializations.bool_op("?|")(array(sorted(specializations))))
            .where(VacancyModel.skills.bool_op("?|")(array(sorted(skills))))
        )
        result = await self._session.execute(query)
        return [vacancy_from_model(model) for model in result.scalars().all()]

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

    async def get_by_content_hash(self, content_hash: ContentHash) -> Vacancy | None:
        result = await self._session.execute(
            select(VacancyModel).where(VacancyModel.content_hash == content_hash.value)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return vacancy_from_model(model)

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
