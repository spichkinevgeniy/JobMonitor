"""Какие фильтры пропустили вакансию только потому, что в ней нет поля."""

from typing import Any
from uuid import uuid4

from app.domain.matching.entities import MatchRejectionReason
from app.domain.matching.policy import unchecked_filters
from app.domain.shared import ExperienceLevel, Grade, WorkFormat
from app.domain.user.entities import User
from app.domain.user.value_objects import FilterMode, LevelFilterMode
from app.domain.vacancy.entities import Vacancy


def _vacancy(**kwargs: Any) -> Vacancy:
    fields: dict[str, Any] = {
        "work_format": WorkFormat.REMOTE,
        "grade": Grade.MIDDLE,
        "experience_level": ExperienceLevel.THREE_TO_SIX_YEARS,
        "salary_amount": 100,
    }
    return Vacancy.create(
        vacancy_id=uuid4(),
        text="Python-разработчик в платёжную команду",
        specializations_raw=["Backend"],
        skills_raw=["Python"],
        mirror_chat_id=1,
        mirror_message_id=1,
        **{**fields, **kwargs},
    )


def _user(**kwargs: Any) -> User:
    return User.create(
        tg_id=1,
        cv_specializations_raw=["Backend"],
        cv_skills_raw=["Python"],
        **kwargs,
    )


def _strict_user() -> User:
    return _user(
        cv_work_format=WorkFormat.REMOTE,
        filter_work_format_mode=FilterMode.STRICT,
        cv_grade=Grade.MIDDLE,
        filter_grade_mode=LevelFilterMode.UP_TO,
        cv_experience_level=ExperienceLevel.THREE_TO_SIX_YEARS,
        filter_experience_mode=LevelFilterMode.EXACT,
        cv_salary_amount=200_000,
        filter_salary_mode=FilterMode.STRICT,
    )


def test_silent_when_vacancy_states_everything() -> None:
    assert unchecked_filters(_vacancy(), _strict_user()) == []


def test_unstated_format_reported_for_strict_filter() -> None:
    unchecked = unchecked_filters(
        _vacancy(work_format=WorkFormat.UNDEFINED),
        _user(cv_work_format=WorkFormat.REMOTE, filter_work_format_mode=FilterMode.STRICT),
    )

    assert unchecked == [MatchRejectionReason.FORMAT]


def test_unstated_format_silent_for_soft_filter() -> None:
    """Фильтр мягкий — вакансия прошла бы в любом случае, объяснять нечего."""
    unchecked = unchecked_filters(
        _vacancy(work_format=WorkFormat.UNDEFINED),
        _user(cv_work_format=WorkFormat.REMOTE, filter_work_format_mode=FilterMode.SOFT),
    )

    assert unchecked == []


def test_unstated_grade_reported() -> None:
    unchecked = unchecked_filters(
        _vacancy(grade=Grade.UNDEFINED),
        _user(cv_grade=Grade.MIDDLE, filter_grade_mode=LevelFilterMode.UP_TO),
    )

    assert unchecked == [MatchRejectionReason.GRADE]


def test_unstated_experience_reported() -> None:
    unchecked = unchecked_filters(
        _vacancy(experience_level=ExperienceLevel.UNDEFINED),
        _user(
            cv_experience_level=ExperienceLevel.ONE_TO_THREE_YEARS,
            filter_experience_mode=LevelFilterMode.EXACT,
        ),
    )

    assert unchecked == [MatchRejectionReason.EXPERIENCE]


def test_unstated_salary_reported() -> None:
    unchecked = unchecked_filters(
        _vacancy(salary_amount=None),
        _user(cv_salary_amount=200_000, filter_salary_mode=FilterMode.STRICT),
    )

    assert unchecked == [MatchRejectionReason.SALARY]


def test_salary_filter_without_amount_is_silent() -> None:
    """Валюта без суммы — фильтру не с чем сравнивать, объяснять нечего."""
    unchecked = unchecked_filters(
        _vacancy(salary_amount=None),
        _user(cv_salary_currency="RUB", filter_salary_mode=FilterMode.STRICT),
    )

    assert unchecked == []


def test_several_come_in_explanation_order() -> None:
    unchecked = unchecked_filters(
        _vacancy(work_format=WorkFormat.UNDEFINED, salary_amount=None),
        _strict_user(),
    )

    assert unchecked == [MatchRejectionReason.FORMAT, MatchRejectionReason.SALARY]
