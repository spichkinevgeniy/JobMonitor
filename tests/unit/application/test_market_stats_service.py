"""Срез рынка: что показываем и что прячем."""

from datetime import UTC, datetime, timedelta

import pytest

from app.application.services.market_stats_service import (
    COUNT_WINDOW,
    MIN_SALARY_SAMPLE,
    SALARY_WINDOW,
    TOP_SKILLS,
    MarketStatsService,
    build_snapshot,
)
from app.domain.vacancy.market import MarketAggregates, SalarySample

NOW = datetime(2026, 9, 28, 19, 0, tzinfo=UTC)


def aggregates(**overrides: object) -> MarketAggregates:
    base: dict[str, object] = {
        "vacancies": 2251,
        "with_salary": 810,
        "channels": 105,
        "by_specialization": {"QA": 291, "Backend": 892, "Mobile": 77},
        "by_work_format": {"REMOTE": 1229, "HYBRID": 408, "ONSITE": 353, "UNDEFINED": 261},
        "by_skill": {"Python": 509, "SQL": 426},
        "salary_by_specialization": {
            "Backend": SalarySample(235000, 561),
            "QA": SalarySample(180000, 370),
            "Mobile": SalarySample(250000, 9),
        },
        "salary_by_specialization_grade": {
            ("Backend", "JUNIOR"): SalarySample(80000, 36),
            ("Backend", "LEAD"): SalarySample(380000, 51),
            ("QA", "JUNIOR"): SalarySample(700000, 9),
        },
        "all_time": 13448,
    }
    base.update(overrides)
    return MarketAggregates(**base)  # type: ignore[arg-type]


class TestDirections:
    def test_sorted_by_vacancies(self) -> None:
        snapshot = build_snapshot(aggregates(), NOW)

        assert [item.specialization for item in snapshot.directions] == ["Backend", "QA", "Mobile"]

    def test_small_salary_sample_is_hidden(self) -> None:
        """Медиана по девяти вакансиям — случайная цифра, а не рынок."""
        snapshot = build_snapshot(aggregates(), NOW)
        mobile = next(item for item in snapshot.directions if item.specialization == "Mobile")

        assert mobile.salary_median is None

    def test_enough_sample_is_shown(self) -> None:
        snapshot = build_snapshot(aggregates(), NOW)

        assert snapshot.directions[0].salary_median == 235000


class TestGradeSalaries:
    def test_cells_follow_grade_order(self) -> None:
        snapshot = build_snapshot(aggregates(), NOW)
        backend = snapshot.grade_salaries[0]

        assert backend.specialization == "Backend"
        assert backend.medians == (80000, None, None, 380000)

    def test_row_of_only_dashes_is_dropped(self) -> None:
        """У QA единственная медиана посчитана по девяти вакансиям."""
        snapshot = build_snapshot(aggregates(), NOW)

        assert [row.specialization for row in snapshot.grade_salaries] == ["Backend"]

    def test_threshold_is_inclusive(self) -> None:
        agg = aggregates(
            salary_by_specialization_grade={
                ("QA", "MIDDLE"): SalarySample(189000, MIN_SALARY_SAMPLE)
            }
        )

        assert build_snapshot(agg, NOW).grade_salaries[0].medians[1] == 189000


class TestShares:
    def test_formats_in_fixed_order(self) -> None:
        snapshot = build_snapshot(aggregates(), NOW)

        assert [(item.key, item.percent) for item in snapshot.formats] == [
            ("REMOTE", 55),
            ("HYBRID", 18),
            ("ONSITE", 16),
            ("UNDEFINED", 12),
        ]

    def test_missing_format_is_zero(self) -> None:
        snapshot = build_snapshot(aggregates(by_work_format={"REMOTE": 10}, vacancies=10), NOW)

        assert [item.percent for item in snapshot.formats] == [100, 0, 0, 0]

    def test_skills_limited_to_top(self) -> None:
        skills = {f"skill{i:02d}": 100 - i for i in range(20)}
        snapshot = build_snapshot(aggregates(by_skill=skills), NOW)

        assert len(snapshot.skills) == TOP_SKILLS
        assert snapshot.skills[0].key == "skill00"

    def test_skill_share_of_all_vacancies(self) -> None:
        snapshot = build_snapshot(aggregates(), NOW)

        assert (snapshot.skills[0].key, snapshot.skills[0].percent) == ("Python", 23)

    def test_salary_percent(self) -> None:
        assert build_snapshot(aggregates(), NOW).salary_percent == 36

    def test_empty_market_has_no_division_by_zero(self) -> None:
        agg = aggregates(
            vacancies=0,
            with_salary=0,
            by_specialization={},
            by_work_format={},
            by_skill={},
            salary_by_specialization={},
            salary_by_specialization_grade={},
        )

        snapshot = build_snapshot(agg, NOW)

        assert snapshot.salary_percent == 0
        assert snapshot.directions == []
        assert all(item.percent == 0 for item in snapshot.formats)


class FakeRepository:
    def __init__(self) -> None:
        self.calls: list[tuple[datetime, datetime]] = []

    async def market_aggregates(
        self, counts_since: datetime, salary_since: datetime
    ) -> MarketAggregates:
        self.calls.append((counts_since, salary_since))
        return aggregates()


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.vacancies = FakeRepository()

    async def __aenter__(self) -> "FakeUnitOfWork":
        return self

    async def __aexit__(self, *exc: object) -> None:
        return None


@pytest.mark.asyncio
async def test_service_uses_both_windows() -> None:
    """Зарплаты за вдвое более длинное окно: иначе медиан почти нет."""
    uow = FakeUnitOfWork()

    snapshot = await MarketStatsService(uow).build_snapshot(NOW)  # type: ignore[arg-type]

    assert uow.vacancies.calls == [(NOW - COUNT_WINDOW, NOW - SALARY_WINDOW)]
    assert SALARY_WINDOW == 2 * COUNT_WINDOW == timedelta(days=56)
    assert snapshot.generated_at == NOW
