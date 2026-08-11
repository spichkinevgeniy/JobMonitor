"""Метрики, у которых источник истины — база.

Считаются запросом, а не накапливаются в памяти, поэтому перезапуск
процесса на них никак не влияет. Все запросы агрегирующие, по таблицам в
тысячи строк — доли миллисекунды.
"""

from dataclasses import dataclass, field

from sqlalchemy import func, select, true
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infrastructure.db.models import User, Vacancy, VacancyDispatchLog


@dataclass(frozen=True, slots=True)
class DbSnapshot:
    users_total: int = 0
    users_active: int = 0
    users_with_profile: int = 0
    users_without_dispatch: int = 0
    avg_skills_per_profile: float = 0.0
    vacancies_dispatched: int = 0
    dispatched_by_specialization: dict[str, int] = field(default_factory=dict)
    dispatched_by_skill: dict[str, int] = field(default_factory=dict)
    feedback_by_verdict: dict[str, int] = field(default_factory=dict)


async def collect_db_snapshot(session_factory: async_sessionmaker[AsyncSession]) -> DbSnapshot:
    async with session_factory() as session:
        users_total, users_active, users_with_profile, avg_skills = (
            await session.execute(
                select(
                    func.count(),
                    func.count().filter(User.is_active.is_(True)),
                    func.count().filter(func.jsonb_array_length(User.cv_specializations) > 0),
                    func.coalesce(
                        func.avg(func.jsonb_array_length(User.cv_skills)).filter(
                            func.jsonb_array_length(User.cv_specializations) > 0
                        ),
                        0,
                    ),
                )
            )
        ).one()

        # Пользователи, которым бот не отправил ни одной вакансии. Отдельным
        # запросом: в агрегат выше подзапрос не встроить без корреляции.
        users_without_dispatch = (
            await session.execute(
                select(func.count())
                .select_from(User)
                .where(
                    ~select(VacancyDispatchLog.id)
                    .where(VacancyDispatchLog.user_tg_id == User.tg_id)
                    .exists()
                )
            )
        ).scalar_one()

        vacancies_dispatched = (
            await session.execute(select(func.count()).select_from(VacancyDispatchLog))
        ).scalar_one()

        # Боковое соединение обязательно: без него получится декартово
        # произведение, и числа разъедутся.
        specialization = (
            func.jsonb_array_elements_text(Vacancy.specializations).table_valued("value").lateral()
        )
        by_specialization = (
            await session.execute(
                select(specialization.c.value, func.count())
                .select_from(VacancyDispatchLog)
                .join(Vacancy, Vacancy.id == VacancyDispatchLog.vacancy_id)
                .join(specialization, true())
                .group_by(specialization.c.value)
            )
        ).all()

        skill = (
            func.jsonb_array_elements_text(VacancyDispatchLog.matched_skills)
            .table_valued("value")
            .lateral()
        )
        by_skill = (
            await session.execute(
                select(skill.c.value, func.count())
                .select_from(VacancyDispatchLog)
                .join(skill, true())
                .group_by(skill.c.value)
            )
        ).all()

        by_verdict = (
            await session.execute(
                select(VacancyDispatchLog.feedback, func.count())
                .where(VacancyDispatchLog.feedback.is_not(None))
                .group_by(VacancyDispatchLog.feedback)
            )
        ).all()

    return DbSnapshot(
        users_total=int(users_total),
        users_active=int(users_active),
        users_with_profile=int(users_with_profile),
        users_without_dispatch=int(users_without_dispatch),
        avg_skills_per_profile=round(float(avg_skills), 2),
        vacancies_dispatched=int(vacancies_dispatched),
        dispatched_by_specialization={row[0]: int(row[1]) for row in by_specialization},
        dispatched_by_skill={row[0]: int(row[1]) for row in by_skill},
        feedback_by_verdict={row[0]: int(row[1]) for row in by_verdict},
    )
