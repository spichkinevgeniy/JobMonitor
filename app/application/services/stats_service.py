from collections import Counter
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from app.application.ports.unit_of_work import VacancyUnitOfWork
from app.domain.matching.policy import evaluate_match
from app.domain.shared.value_objects import CompanyType
from app.domain.user.entities import User
from app.domain.vacancy.entities import Vacancy

WEEK_DAYS = 7
TREND_WEEKS = 8
COMPANY_BREAKDOWN_DAYS = 30


@dataclass(frozen=True, slots=True)
class TrendPoint:
    week_start: date
    count: int


@dataclass(frozen=True, slots=True)
class CompanyTypeCount:
    company_type: CompanyType
    count: int


@dataclass(frozen=True, slots=True)
class ProfileStats:
    current_week_count: int
    previous_week_count: int
    trend: list[TrendPoint]
    company_breakdown: list[CompanyTypeCount]
    company_total: int


class StatsService:
    """Read-only аналитика поверх уже собранных вакансий.

    Считает то же самое, что решает реальная рассылка: SQL-префильтр по
    специализациям и скиллам + evaluate_match по остальным фильтрам профиля.
    """

    def __init__(self, uow: VacancyUnitOfWork) -> None:
        self._uow = uow

    async def build_profile_stats(self, user: User) -> ProfileStats:
        now = datetime.now(UTC)
        since = now - timedelta(days=TREND_WEEKS * WEEK_DAYS)

        async with self._uow:
            vacancies = await self._uow.vacancies.find_for_profile_since(
                specializations={item.value for item in user.cv_specializations.items},
                skills={item.value for item in user.cv_skills.items},
                since=since,
            )

        matched = [item for item in vacancies if evaluate_match(vacancy=item, user=user).accepted]
        company_breakdown = _build_company_breakdown(matched, now)

        return ProfileStats(
            current_week_count=_count_between(
                matched,
                now - timedelta(days=WEEK_DAYS),
                now,
            ),
            previous_week_count=_count_between(
                matched,
                now - timedelta(days=2 * WEEK_DAYS),
                now - timedelta(days=WEEK_DAYS),
            ),
            trend=_build_trend(matched, now),
            company_breakdown=company_breakdown,
            company_total=sum(item.count for item in company_breakdown),
        )


def _count_between(vacancies: list[Vacancy], start: datetime, end: datetime) -> int:
    return sum(1 for item in vacancies if start <= item.created_at < end)


def _build_trend(vacancies: list[Vacancy], now: datetime) -> list[TrendPoint]:
    points: list[TrendPoint] = []
    for index in reversed(range(TREND_WEEKS)):
        end = now - timedelta(days=index * WEEK_DAYS)
        start = end - timedelta(days=WEEK_DAYS)
        points.append(
            TrendPoint(
                week_start=start.date(),
                count=_count_between(vacancies, start, end),
            )
        )
    return points


def _build_company_breakdown(vacancies: list[Vacancy], now: datetime) -> list[CompanyTypeCount]:
    window_start = now - timedelta(days=COMPANY_BREAKDOWN_DAYS)
    counter = Counter(
        item.company_type for item in vacancies if window_start <= item.created_at < now
    )
    return [
        CompanyTypeCount(company_type=company_type, count=count)
        for company_type, count in counter.most_common()
    ]
