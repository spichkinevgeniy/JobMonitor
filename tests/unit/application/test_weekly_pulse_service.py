"""Недельная сводка: календарная неделя по Москве и пороги, ниже которых цифрам не верим."""

from datetime import UTC, date, datetime, timedelta
from types import TracebackType
from typing import Any
from uuid import uuid4

from app.application.services.weekly_pulse_service import (
    MIN_SALARY_SAMPLE,
    MIN_WEEKLY_MATCHES,
    SALARY_WINDOW_DAYS,
    WeeklyPulse,
    WeeklyPulseService,
    last_full_week,
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

# Среда: прошедшая неделя — 21–27 сентября по Москве.
WEEK = last_full_week(datetime(2026, 9, 30, 12, tzinfo=UTC))


def _vacancy(created_at: datetime, specialization: str = "Backend") -> Vacancy:
    return Vacancy(
        id=VacancyId(uuid4()),
        text="vacancy",
        specializations=Specializations.from_strs([specialization]),
        skills=Skills.from_strs(["Python"]),
        mirror_chat_id=1,
        mirror_message_id=1,
        salary=Salary.create(None, None),
        grade=Grade.MIDDLE,
        experience_level=ExperienceLevel.UNDEFINED,
        work_format=WorkFormat.REMOTE,
        company_type=CompanyType.UNDEFINED,
        content_hash=ContentHash(f"hash-{uuid4()}"),
        created_at=created_at,
        is_active=True,
    )


def _user(specializations: list[str] | None = None, grade: str | None = "MIDDLE") -> User:
    return User.create(
        tg_id=42,
        cv_specializations_raw=specializations or ["Backend"],
        cv_skills_raw=["Python"],
        cv_grade=grade,
    )


class _FakeVacancies:
    def __init__(
        self,
        vacancies: list[Vacancy],
        medians: dict[str, tuple[int | None, int]] | None = None,
    ) -> None:
        self._vacancies = vacancies
        self._medians = medians or {}
        self.median_calls: list[dict[str, Any]] = []

    async def find_for_profile_since(
        self, specializations: set[str], skills: set[str], since: datetime
    ) -> list[Vacancy]:
        return [
            item
            for item in self._vacancies
            if item.created_at >= since
            and {s.value for s in item.specializations.items} & specializations
            and {s.value for s in item.skills.items} & skills
        ]

    async def find_for_specializations_since(
        self, specializations: set[str], since: datetime
    ) -> list[Vacancy]:
        return [
            item
            for item in self._vacancies
            if item.created_at >= since
            and {s.value for s in item.specializations.items} & specializations
        ]

    async def count_dispatches_between(
        self, user_tg_id: int, since: datetime, until: datetime
    ) -> tuple[int, int]:
        return 18, 2

    async def salary_median(
        self, specialization: str, grade: str | None, since: datetime, until: datetime
    ) -> tuple[int | None, int]:
        self.median_calls.append(
            {"specialization": specialization, "grade": grade, "since": since, "until": until}
        )
        return self._medians.get(specialization, (None, 0))


class _FakeUow:
    def __init__(self, vacancies: _FakeVacancies) -> None:
        self.vacancies = vacancies

    async def __aenter__(self) -> "_FakeUow":
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


def _in_week(count: int, week_start: datetime) -> list[Vacancy]:
    return [_vacancy(week_start + timedelta(hours=5 + index * 10)) for index in range(count)]


async def _build(
    vacancies: list[Vacancy],
    user: User | None = None,
    medians: dict[str, tuple[int | None, int]] | None = None,
) -> tuple[WeeklyPulse, _FakeVacancies]:
    repo = _FakeVacancies(vacancies, medians)
    service = WeeklyPulseService(_FakeUow(repo))  # type: ignore[arg-type]
    return await service.build(user or _user(), WEEK), repo


def test_week_is_monday_to_monday_in_moscow() -> None:
    assert WEEK.start == datetime(2026, 9, 20, 21, tzinfo=UTC)
    assert WEEK.end == datetime(2026, 9, 27, 21, tzinfo=UTC)
    assert WEEK.start_date == date(2026, 9, 21)
    assert WEEK.last_date == date(2026, 9, 27)


def test_monday_night_already_belongs_to_the_new_week() -> None:
    """00:30 понедельника по Москве — ещё воскресенье по UTC."""
    monday_night = datetime(2026, 9, 27, 21, 30, tzinfo=UTC)
    sunday_evening = datetime(2026, 9, 27, 20, 30, tzinfo=UTC)

    assert last_full_week(monday_night).end == datetime(2026, 9, 27, 21, tzinfo=UTC)
    assert last_full_week(sunday_evening).end == datetime(2026, 9, 20, 21, tzinfo=UTC)


async def test_counts_only_the_calendar_week() -> None:
    """Вакансии понедельника, пришедшие до отправки, в прошлую неделю не попадают."""
    vacancies = (
        _in_week(12, WEEK.start)
        + _in_week(5, WEEK.start - timedelta(weeks=1))
        + [_vacancy(WEEK.end), _vacancy(WEEK.end + timedelta(hours=9))]
    )

    pulse, _ = await _build(vacancies)

    assert pulse.matched == 12
    assert pulse.matched_previous == 5


async def test_fewer_than_ten_matches_is_not_worth_sending() -> None:
    below, _ = await _build(_in_week(MIN_WEEKLY_MATCHES - 1, WEEK.start))
    enough, _ = await _build(_in_week(MIN_WEEKLY_MATCHES, WEEK.start))

    assert not below.worth_sending
    assert enough.worth_sending


async def test_dispatches_come_from_the_repository() -> None:
    pulse, _ = await _build(_in_week(10, WEEK.start))

    assert (pulse.sent, pulse.rejected) == (18, 2)


async def test_salary_median_needs_ten_vacancies() -> None:
    few, _ = await _build([], medians={"Backend": (185_000, MIN_SALARY_SAMPLE - 1)})
    enough, _ = await _build([], medians={"Backend": (185_000, MIN_SALARY_SAMPLE)})

    assert few.salary is None
    assert enough.salary is not None
    assert enough.salary.amount == 185_000
    assert enough.salary.grade is Grade.MIDDLE


async def test_salary_uses_four_weeks_before_the_week_end() -> None:
    _, repo = await _build([], medians={"Backend": (185_000, 20)})

    assert repo.median_calls == [
        {
            "specialization": "Backend",
            "grade": "MIDDLE",
            "since": WEEK.end - timedelta(days=SALARY_WINDOW_DAYS),
            "until": WEEK.end,
        }
    ]


async def test_salary_takes_the_specialization_with_more_data() -> None:
    pulse, _ = await _build(
        [],
        user=_user(["Backend", "QA"]),
        medians={"Backend": (200_000, 15), "QA": (150_000, 40)},
    )

    assert pulse.salary is not None
    assert pulse.salary.specialization == "QA"


async def test_without_grade_median_covers_whole_specialization() -> None:
    pulse, repo = await _build([], user=_user(grade=None), medians={"Backend": (190_000, 30)})

    assert repo.median_calls[0]["grade"] is None
    assert pulse.salary is not None
    assert pulse.salary.grade is None
