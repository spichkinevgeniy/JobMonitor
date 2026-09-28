"""Срез рынка для публичной страницы: что показывать и что прятать."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.application.ports.unit_of_work import VacancyUnitOfWork
from app.domain.shared.value_objects import Grade, WorkFormat
from app.domain.vacancy.market import MarketAggregates, SalarySample

COUNT_WINDOW = timedelta(days=28)
# Зарплату указывают в каждой третьей вакансии, и за четыре недели
# по небольшим направлениям медиан не набирается.
SALARY_WINDOW = timedelta(days=56)
# Медиана по меньшей выборке — случайная цифра: на проде так выходил
# junior-аналитик за 700 тысяч по девяти вакансиям.
MIN_SALARY_SAMPLE = 10
TOP_SKILLS = 12
SHOWN_GRADES = (Grade.JUNIOR, Grade.MIDDLE, Grade.SENIOR, Grade.LEAD)
FORMAT_ORDER = (WorkFormat.REMOTE, WorkFormat.HYBRID, WorkFormat.ONSITE, WorkFormat.UNDEFINED)


@dataclass(frozen=True, slots=True)
class DirectionStat:
    specialization: str
    vacancies: int
    salary_median: int | None


@dataclass(frozen=True, slots=True)
class GradeSalaryRow:
    specialization: str
    # По грейдам из SHOWN_GRADES; None — выборка слишком мала.
    medians: tuple[int | None, ...]


@dataclass(frozen=True, slots=True)
class Share:
    key: str
    percent: int


@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    generated_at: datetime
    vacancies: int
    salary_percent: int
    channels: int
    all_time: int
    directions: list[DirectionStat]
    grade_salaries: list[GradeSalaryRow]
    formats: list[Share]
    skills: list[Share]


class MarketStatsService:
    def __init__(self, uow: VacancyUnitOfWork) -> None:
        self._uow = uow

    async def build_snapshot(self, now: datetime | None = None) -> MarketSnapshot:
        now = now or datetime.now(UTC)
        async with self._uow:
            aggregates = await self._uow.vacancies.market_aggregates(
                counts_since=now - COUNT_WINDOW,
                salary_since=now - SALARY_WINDOW,
            )
        return build_snapshot(aggregates, now)


def build_snapshot(aggregates: MarketAggregates, now: datetime) -> MarketSnapshot:
    directions = sorted(
        (
            DirectionStat(
                specialization=name,
                vacancies=count,
                salary_median=_usable(aggregates.salary_by_specialization.get(name)),
            )
            for name, count in aggregates.by_specialization.items()
        ),
        key=lambda item: (-item.vacancies, item.specialization),
    )

    grade_salaries = []
    for direction in directions:
        medians = tuple(
            _usable(
                aggregates.salary_by_specialization_grade.get(
                    (direction.specialization, grade.value)
                )
            )
            for grade in SHOWN_GRADES
        )
        # Строка из одних прочерков ничего не сообщает.
        if any(value is not None for value in medians):
            grade_salaries.append(GradeSalaryRow(direction.specialization, medians))

    total = aggregates.vacancies
    formats = [
        Share(item.value, _percent(aggregates.by_work_format.get(item.value, 0), total))
        for item in FORMAT_ORDER
    ]
    top_skills = sorted(aggregates.by_skill.items(), key=lambda item: (-item[1], item[0]))
    skills = [Share(name, _percent(count, total)) for name, count in top_skills[:TOP_SKILLS]]

    return MarketSnapshot(
        generated_at=now,
        vacancies=total,
        salary_percent=_percent(aggregates.with_salary, total),
        channels=aggregates.channels,
        all_time=aggregates.all_time,
        directions=directions,
        grade_salaries=grade_salaries,
        formats=formats,
        skills=skills,
    )


def _usable(sample: SalarySample | None) -> int | None:
    if sample is None or sample.median is None or sample.sample < MIN_SALARY_SAMPLE:
        return None
    return sample.median


def _percent(part: int, total: int) -> int:
    return round(100 * part / total) if total else 0
