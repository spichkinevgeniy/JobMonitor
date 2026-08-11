"""Тесты аналитики на обезличенном срезе реальных прод-данных.

Фикстуры собраны из настоящей базы: 60 профилей со всеми реально
встречающимися комбинациями фильтров и 343 вакансии, равномерно
растянутые на 8 недель. Время в фикстурах хранится как «часов назад»,
поэтому данные всегда попадают в окна аналитики.
"""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import TracebackType
from typing import Any
from uuid import uuid4

import pytest

from app.application.services.stats_service import (
    COMPANY_BREAKDOWN_DAYS,
    FUNNEL_DAYS,
    TREND_DAYS,
    TREND_WEEKS,
    ProfileStats,
    StatsService,
)
from app.domain.shared.value_objects import (
    CompanyType,
    ExperienceLevel,
    Grade,
    Salary,
    Skills,
    Specializations,
    WorkFormat,
)
from app.domain.user.entities import User
from app.domain.vacancy.entities import Vacancy
from app.domain.vacancy.value_objects import ContentHash, VacancyId

FIXTURES_DIR = Path(__file__).parents[2] / "fixtures"


def _load(name: str) -> list[dict[str, Any]]:
    data: list[dict[str, Any]] = json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))
    return data


PROFILE_ROWS = _load("anonymized_profiles.json")
VACANCY_ROWS = _load("anonymized_vacancies.json")


def _build_user(row: dict[str, Any]) -> User:
    return User.create(
        tg_id=row["tg_id"],
        cv_specializations_raw=row["specializations"],
        cv_skills_raw=row["skills"],
        cv_salary_amount=row["salary_amount"],
        cv_salary_currency=row["salary_currency"],
        filter_salary_mode=row["salary_mode"],
        cv_grade=row["grade"],
        filter_grade_mode=row["grade_mode"],
        cv_experience_level=row["experience_level"],
        filter_experience_mode=row["experience_mode"],
        cv_work_format=row["work_format"],
        filter_work_format_mode=row["work_format_mode"],
    )


def _build_vacancies(now: datetime) -> list[Vacancy]:
    """Собираем как маппер при чтении из БД, а не через Vacancy.create.

    В проде есть строки с пустыми skills/specializations — их оставила
    миграция c9e1f2a3b4d5, вычищавшая устаревшие теги. Vacancy.create такое
    запрещает, но читаются они нормально, поэтому фикстуры должны их
    воспроизводить: аналитика обязана их корректно игнорировать.
    """
    vacancies: list[Vacancy] = []
    for index, row in enumerate(VACANCY_ROWS):
        vacancies.append(
            Vacancy(
                id=VacancyId(uuid4()),
                text=f"vacancy {index}",
                specializations=Specializations.from_strs(row["specializations"]),
                skills=Skills.from_strs(row["skills"]),
                mirror_chat_id=1,
                mirror_message_id=index,
                salary=Salary.create(row["salary_amount"], row["salary_currency"]),
                grade=Grade(row["grade"]),
                experience_level=ExperienceLevel(row["experience_level"]),
                work_format=WorkFormat(row["work_format"]),
                company_type=CompanyType(row["company_type"]),
                content_hash=ContentHash(f"hash-{index}"),
                created_at=now - timedelta(hours=row["hours_ago"]),
                is_active=True,
            )
        )
    return vacancies


class _FakeVacancyRepository:
    """Повторяет семантику SQL-префильтра из VacancyRepository.

    В боевом запросе это пересечение JSONB-массивов по специализациям И по
    скиллам плюс окно по created_at, поэтому здесь так же.
    """

    def __init__(self, vacancies: list[Vacancy]) -> None:
        self._vacancies = vacancies

    async def find_for_profile_since(
        self,
        specializations: set[str],
        skills: set[str],
        since: datetime,
    ) -> list[Vacancy]:
        if not specializations or not skills:
            return []

        return [
            vacancy
            for vacancy in self._vacancies
            if vacancy.is_active
            and vacancy.created_at >= since
            and {item.value for item in vacancy.specializations.items} & specializations
            and {item.value for item in vacancy.skills.items} & skills
        ]

    async def find_for_specializations_since(
        self,
        specializations: set[str],
        since: datetime,
    ) -> list[Vacancy]:
        if not specializations:
            return []

        return [
            vacancy
            for vacancy in self._vacancies
            if vacancy.is_active
            and vacancy.created_at >= since
            and {item.value for item in vacancy.specializations.items} & specializations
        ]


class _FakeVacancyUnitOfWork:
    def __init__(self, vacancies: list[Vacancy]) -> None:
        self.vacancies = _FakeVacancyRepository(vacancies)

    async def __aenter__(self) -> "_FakeVacancyUnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None


async def _build_stats(user: User) -> ProfileStats:
    vacancies = _build_vacancies(datetime.now(UTC))
    service = StatsService(_FakeVacancyUnitOfWork(vacancies))  # type: ignore[arg-type]
    return await service.build_profile_stats(user)


ALL_PROFILES = [pytest.param(row, id=f"profile-{row['tg_id']}") for row in PROFILE_ROWS]


@pytest.mark.asyncio
@pytest.mark.parametrize("row", ALL_PROFILES)
async def test_funnel_rows_sum_to_total(row: dict[str, Any]) -> None:
    """Воронка обязана сходиться: иначе проценты в UI соврут."""
    stats = await _build_stats(_build_user(row))
    funnel = stats.funnel

    rejected = sum(item.count for item in funnel.rejections)
    assert funnel.matched + rejected == funnel.total


@pytest.mark.asyncio
@pytest.mark.parametrize("row", ALL_PROFILES)
async def test_funnel_matched_equals_last_week_bar(row: dict[str, Any]) -> None:
    """Воронка и график считают одно и то же — числа не должны расходиться."""
    stats = await _build_stats(_build_user(row))
    week_series = next(item for item in stats.trends if item.granularity.value == "week")

    assert week_series.points[-1].count == stats.funnel.matched


@pytest.mark.asyncio
@pytest.mark.parametrize("row", ALL_PROFILES)
async def test_last_seven_days_match_last_week_bucket(row: dict[str, Any]) -> None:
    """Дневная и недельная гранулярности обязаны сходиться между собой."""
    stats = await _build_stats(_build_user(row))
    by_granularity = {item.granularity.value: item for item in stats.trends}

    last_seven_days = sum(point.count for point in by_granularity["day"].points[-FUNNEL_DAYS:])
    assert last_seven_days == by_granularity["week"].points[-1].count


@pytest.mark.asyncio
@pytest.mark.parametrize("row", ALL_PROFILES)
async def test_trend_always_has_fixed_number_of_points(row: dict[str, Any]) -> None:
    """График рисуется по фиксированной сетке, даже если данных нет."""
    stats = await _build_stats(_build_user(row))
    by_granularity = {item.granularity.value: item for item in stats.trends}

    assert len(by_granularity["week"].points) == TREND_WEEKS
    assert len(by_granularity["day"].points) == TREND_DAYS


@pytest.mark.asyncio
@pytest.mark.parametrize("row", ALL_PROFILES)
async def test_company_breakdown_sums_to_total(row: dict[str, Any]) -> None:
    stats = await _build_stats(_build_user(row))

    assert stats.company_total == sum(item.count for item in stats.company_breakdown)


@pytest.mark.asyncio
@pytest.mark.parametrize("row", ALL_PROFILES)
async def test_counts_are_never_negative(row: dict[str, Any]) -> None:
    stats = await _build_stats(_build_user(row))

    assert stats.funnel.total >= 0
    assert stats.funnel.matched >= 0
    assert all(item.count >= 0 for item in stats.funnel.rejections)
    assert all(point.count >= 0 for series in stats.trends for point in series.points)


@pytest.mark.asyncio
@pytest.mark.parametrize("row", ALL_PROFILES)
async def test_wider_window_is_never_smaller(row: dict[str, Any]) -> None:
    """30-дневное окно не может содержать меньше, чем 7-дневное."""
    stats = await _build_stats(_build_user(row))
    week_series = next(item for item in stats.trends if item.granularity.value == "week")

    assert COMPANY_BREAKDOWN_DAYS >= FUNNEL_DAYS
    assert stats.company_total >= week_series.points[-1].count


@pytest.mark.asyncio
async def test_empty_profile_yields_zeros() -> None:
    """Профиль без специализаций и скиллов — самая частая форма в проде."""
    empty_rows = [row for row in PROFILE_ROWS if not row["specializations"] and not row["skills"]]
    assert empty_rows, "в фикстурах должен быть хотя бы один пустой профиль"

    stats = await _build_stats(_build_user(empty_rows[0]))

    assert stats.funnel.total == 0
    assert stats.funnel.matched == 0
    assert stats.funnel.rejections == []
    assert stats.company_total == 0
    assert all(point.count == 0 for series in stats.trends for point in series.points)


@pytest.mark.asyncio
async def test_fixtures_cover_every_filter_mode() -> None:
    """Страховка от вырождения фикстур: режимы фильтров должны быть все."""
    salary_modes = {row["salary_mode"] for row in PROFILE_ROWS}
    grade_modes = {row["grade_mode"] for row in PROFILE_ROWS}
    experience_modes = {row["experience_mode"] for row in PROFILE_ROWS}
    format_modes = {row["work_format_mode"] for row in PROFILE_ROWS}

    assert {"SOFT", "STRICT"} <= salary_modes
    assert {"IGNORE", "UP_TO", "EXACT"} <= grade_modes
    assert {"IGNORE", "UP_TO"} <= experience_modes
    assert {"SOFT", "STRICT"} <= format_modes
