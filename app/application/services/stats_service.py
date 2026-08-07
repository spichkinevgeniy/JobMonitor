from collections import Counter
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from enum import StrEnum

from app.application.ports.unit_of_work import VacancyUnitOfWork
from app.domain.matching.entities import MatchDecision, MatchRejectionReason
from app.domain.matching.policy import evaluate_match
from app.domain.shared.value_objects import CompanyType
from app.domain.user.entities import User
from app.domain.vacancy.entities import Vacancy

WEEK_DAYS = 7
TREND_WEEKS = 8
TREND_DAYS = 14
COMPANY_BREAKDOWN_DAYS = 30
FUNNEL_DAYS = 7

# Подсказку показываем, только если навык открывает заметное число вакансий:
# иначе в хвост списка лезут случайные совпадения вроде Machine Learning
# у фронтендера.
MIN_SUGGESTION_UNLOCKS = 3
MAX_SUGGESTIONS = 3

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
class RejectionCount:
    reason: MatchRejectionReason
    count: int


@dataclass(frozen=True, slots=True)
class FilterFunnel:
    """Куда делись вакансии, прошедшие префильтр по специализации и скиллам.

    matched + сумма rejections == total: evaluate_match возвращает первую
    сработавшую причину, поэтому каждая вакансия учтена ровно один раз.
    """

    total: int
    matched: int
    rejections: list[RejectionCount]
    # Сколько было по специализации до префильтра по навыкам и сколько на нём
    # потерялось. Воронка начинается после префильтра и эту часть не видит.
    specialization_total: int = 0
    skills_mismatch: int = 0


@dataclass(frozen=True, slots=True)
class SkillSuggestion:
    skill: str
    unlocks: int


@dataclass(frozen=True, slots=True)
class ProfileStats:
    trends: list[TrendSeries]
    company_breakdown: list[CompanyTypeCount]
    company_total: int
    funnel: FilterFunnel
    skill_suggestions: list[SkillSuggestion]


class StatsService:
    """Read-only аналитика поверх уже собранных вакансий.

    Считает то же самое, что решает реальная рассылка: SQL-префильтр по
    специализациям и скиллам + evaluate_match по остальным фильтрам профиля.
    """

    def __init__(self, uow: VacancyUnitOfWork) -> None:
        self._uow = uow

    async def build_profile_stats(self, user: User) -> ProfileStats:
        now = datetime.now(UTC)

        specializations = {item.value for item in user.cv_specializations.items}
        skills = {item.value for item in user.cv_skills.items}

        async with self._uow:
            vacancies = await self._uow.vacancies.find_for_profile_since(
                specializations=specializations,
                skills=skills,
                since=now - timedelta(days=FETCH_DAYS),
            )
            # Отдельный запрос на короткое окно: по одной специализации строк
            # набирается в разы больше, тянуть их на 8 недель незачем.
            by_specialization = await self._uow.vacancies.find_for_specializations_since(
                specializations=specializations,
                since=now - timedelta(days=FUNNEL_DAYS),
            )

        # Решение по каждой вакансии считаем один раз: тренды берут принятые,
        # воронка — распределение отказов.
        decisions = [(item, evaluate_match(vacancy=item, user=user)) for item in vacancies]
        matched = [item for item, decision in decisions if decision.accepted]
        company_breakdown = _build_company_breakdown(matched, now)
        unmatched_by_skills = [
            item
            for item in by_specialization
            if not (skills & {s.value for s in item.skills.items})
        ]

        return ProfileStats(
            skill_suggestions=_build_skill_suggestions(unmatched_by_skills, skills, user),
            funnel=_build_funnel(
                decisions,
                now,
                specialization_total=len(by_specialization),
                skills_mismatch=len(unmatched_by_skills),
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


def _build_funnel(
    decisions: list[tuple[Vacancy, MatchDecision]],
    now: datetime,
    *,
    specialization_total: int,
    skills_mismatch: int,
) -> FilterFunnel:
    window_start = now - timedelta(days=FUNNEL_DAYS)
    window = [
        decision for vacancy, decision in decisions if window_start <= vacancy.created_at < now
    ]

    counter: Counter[MatchRejectionReason] = Counter(
        decision.reason
        for decision in window
        if not decision.accepted and decision.reason is not None
    )
    return FilterFunnel(
        total=len(window),
        matched=sum(1 for decision in window if decision.accepted),
        rejections=[
            RejectionCount(reason=reason, count=count) for reason, count in counter.most_common()
        ],
        specialization_total=specialization_total,
        skills_mismatch=skills_mismatch,
    )


def _build_skill_suggestions(
    unmatched: list[Vacancy],
    skills: set[str],
    user: User,
) -> list[SkillSuggestion]:
    """Какие навыки открыли бы больше всего вакансий.

    Считаем только те, что и правда дошли бы: мало добавить навык, вакансия
    должна ещё пройти фильтры по грейду, опыту, формату и зарплате.
    """
    counter: Counter[str] = Counter()
    for vacancy in unmatched:
        if not evaluate_match(vacancy=vacancy, user=user).accepted:
            continue
        for skill in vacancy.skills.items:
            if skill.value not in skills:
                counter[skill.value] += 1

    return [
        SkillSuggestion(skill=skill, unlocks=count)
        for skill, count in counter.most_common(MAX_SUGGESTIONS)
        if count >= MIN_SUGGESTION_UNLOCKS
    ]


def _build_company_breakdown(vacancies: list[Vacancy], now: datetime) -> list[CompanyTypeCount]:
    window_start = now - timedelta(days=COMPANY_BREAKDOWN_DAYS)
    counter = Counter(
        item.company_type for item in vacancies if window_start <= item.created_at < now
    )
    return [
        CompanyTypeCount(company_type=company_type, count=count)
        for company_type, count in counter.most_common()
    ]
