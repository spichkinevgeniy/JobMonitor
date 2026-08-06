from collections import Counter
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from enum import StrEnum

from app.application.ports.unit_of_work import VacancyUnitOfWork
from app.domain.matching.policy import evaluate_match
from app.domain.shared.value_objects import CompanyType
from app.domain.user.entities import User
from app.domain.vacancy.entities import Vacancy

WEEK_DAYS = 7
TREND_WEEKS = 8
TREND_DAYS = 14
COMPANY_BREAKDOWN_DAYS = 30

# Окно выборки берём по самой длинной гранулярности: 8 недель покрывают и 14 дней,
# поэтому на страницу хватает одного запроса в БД.
FETCH_DAYS = max(TREND_WEEKS * WEEK_DAYS, TREND_DAYS, COMPANY_BREAKDOWN_DAYS)


class TrendGranularity(StrEnum):
    WEEK = "week"
    DAY = "day"


@dataclass(frozen=True, slots=True)
class TrendPoint:
    bucket_start: date
    count: int


@dataclass(frozen=True, slots=True)
class TrendSeries:
    granularity: TrendGranularity
    points: list[TrendPoint]


@dataclass(frozen=True, slots=True)
class CompanyTypeCount:
    company_type: CompanyType
    count: int


@dataclass(frozen=True, slots=True)
class ProfileStats:
    current_week_count: int
    trends: list[TrendSeries]
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

        async with self._uow:
            vacancies = await self._uow.vacancies.find_for_profile_since(
                specializations={item.value for item in user.cv_specializations.items},
                skills={item.value for item in user.cv_skills.items},
                since=now - timedelta(days=FETCH_DAYS),
            )

        matched = [item for item in vacancies if evaluate_match(vacancy=item, user=user).accepted]
        company_breakdown = _build_company_breakdown(matched, now)

        return ProfileStats(
            current_week_count=_count_between(
                matched,
                now - timedelta(days=WEEK_DAYS),
                now,
            ),
            trends=[
                TrendSeries(
                    granularity=TrendGranularity.WEEK,
                    points=_build_trend(matched, now, TREND_WEEKS, WEEK_DAYS),
                ),
                TrendSeries(
                    granularity=TrendGranularity.DAY,
                    points=_build_trend(matched, now, TREND_DAYS, 1),
                ),
            ],
            company_breakdown=company_breakdown,
            company_total=sum(item.count for item in company_breakdown),
        )


def _count_between(vacancies: list[Vacancy], start: datetime, end: datetime) -> int:
    return sum(1 for item in vacancies if start <= item.created_at < end)


def _build_trend(
    vacancies: list[Vacancy],
    now: datetime,
    bucket_count: int,
    bucket_days: int,
) -> list[TrendPoint]:
    points: list[TrendPoint] = []
    for index in reversed(range(bucket_count)):
        end = now - timedelta(days=index * bucket_days)
        start = end - timedelta(days=bucket_days)
        points.append(
            TrendPoint(
                bucket_start=start.date(),
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
