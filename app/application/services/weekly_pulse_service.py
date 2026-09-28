"""Недельная сводка по рынку для одного пользователя.

Почти всё уже считает StatsService для мини-аппа: тренд подходящих вакансий
и воронку фильтров. Сводка берёт оттуда прошедшую календарную неделю
и добавляет медиану зарплаты и то, сколько вакансий бот человеку отправил.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta, timezone

from app.application.ports.unit_of_work import VacancyUnitOfWork
from app.application.services.stats_service import (
    RejectionCount,
    StatsService,
    TrendGranularity,
)
from app.domain.shared.value_objects import Grade
from app.domain.user.entities import User

# Москва живёт без перехода на летнее время с 2014 года, а tzdata в образе
# может не оказаться.
MSK = timezone(timedelta(hours=3))

# Меньше десяти вакансий за неделю — это не рынок, а шум: такую сводку
# не отправляем вовсе.
MIN_WEEKLY_MATCHES = 10

# Медиана по нескольким вакансиям ничего не говорит о рынке.
MIN_SALARY_SAMPLE = 10
SALARY_WINDOW_DAYS = 28


@dataclass(frozen=True, slots=True)
class PulseWeek:
    """Неделя с понедельника 00:00 по Москве, границы в UTC."""

    start: datetime
    end: datetime

    @property
    def start_date(self) -> date:
        return self.start.astimezone(MSK).date()

    @property
    def last_date(self) -> date:
        return (self.end - timedelta(days=1)).astimezone(MSK).date()


def last_full_week(now: datetime) -> PulseWeek:
    local = now.astimezone(MSK)
    monday = (local - timedelta(days=local.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return PulseWeek(
        start=(monday - timedelta(weeks=1)).astimezone(UTC),
        end=monday.astimezone(UTC),
    )


@dataclass(frozen=True, slots=True)
class SalaryMedian:
    specialization: str
    grade: Grade | None
    amount: int
    sample: int


@dataclass(frozen=True, slots=True)
class WeeklyPulse:
    week: PulseWeek
    matched: int
    matched_previous: int
    sent: int
    rejected: int
    salary: SalaryMedian | None
    top_rejection: RejectionCount | None

    @property
    def worth_sending(self) -> bool:
        return self.matched >= MIN_WEEKLY_MATCHES


class WeeklyPulseService:
    def __init__(self, uow: VacancyUnitOfWork) -> None:
        self._uow = uow
        self._stats = StatsService(uow)

    async def build(self, user: User, week: PulseWeek) -> WeeklyPulse:
        stats = await self._stats.build_profile_stats(user, now=week.end)
        weekly = next(
            series.points for series in stats.trends if series.granularity is TrendGranularity.WEEK
        )

        async with self._uow:
            sent, rejected = await self._uow.vacancies.count_dispatches_between(
                user.tg_id.value, week.start, week.end
            )
            salary = await self._salary_median(user, week)

        return WeeklyPulse(
            week=week,
            matched=weekly[-1].count,
            matched_previous=weekly[-2].count,
            sent=sent,
            rejected=rejected,
            salary=salary,
            top_rejection=stats.funnel.rejections[0] if stats.funnel.rejections else None,
        )

    async def _salary_median(self, user: User, week: PulseWeek) -> SalaryMedian | None:
        """Медиана по специализации профиля и его грейду.

        Специализаций в профиле может быть несколько, и порядка у них нет:
        берём ту, где вакансий с зарплатой больше, — её медиана надёжнее.
        Без грейда медиана по всей специализации: смешивать junior и lead
        хуже, чем уточнить, но это всё ещё честная цифра рынка.
        """
        grade = user.cv_grade if user.cv_grade not in (None, Grade.UNDEFINED) else None
        best: SalaryMedian | None = None
        for specialization in sorted(item.value for item in user.cv_specializations.items):
            amount, sample = await self._uow.vacancies.salary_median(
                specialization=specialization,
                grade=grade.value if grade else None,
                since=week.end - timedelta(days=SALARY_WINDOW_DAYS),
                until=week.end,
            )
            if amount is None or sample < MIN_SALARY_SAMPLE:
                continue
            if best is None or sample > best.sample:
                best = SalaryMedian(
                    specialization=specialization,
                    grade=grade,
                    amount=amount,
                    sample=sample,
                )
        return best
