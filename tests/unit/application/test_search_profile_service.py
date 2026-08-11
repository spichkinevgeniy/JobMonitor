from datetime import UTC, datetime

import pytest

from app.application.services.search_profile_service import (
    IncompleteSearchProfileError,
    SearchProfileService,
)
from app.domain.shared import Grade
from app.domain.user.entities import User
from app.domain.user.value_objects import FilterMode, LevelFilterMode


def _completed_user(**overrides: object) -> User:
    values: dict[str, object] = {
        "tg_id": 1,
        "cv_specializations_raw": ["Frontend"],
        "cv_skills_raw": ["React", "TypeScript"],
        "cv_work_formats_raw": ["REMOTE", "HYBRID"],
        "cv_salary_amount": 150000,
        "cv_salary_currency": "RUB",
        "filter_salary_mode": FilterMode.STRICT,
        "cv_grade": Grade.JUNIOR,
        "filter_grade_mode": LevelFilterMode.AT_LEAST,
        "onboarding_completed_at": datetime.now(UTC),
        "is_active": True,
    }
    values.update(overrides)
    return User.create(**values)  # type: ignore[arg-type]


def test_profile_uses_canonical_filters_and_preserves_multiple_formats() -> None:
    response = SearchProfileService.get_profile(_completed_user(is_active=False))

    assert response.specializations == ["Frontend"]
    assert response.skills == ["React", "TypeScript"]
    assert response.work_formats == ["HYBRID", "REMOTE"]
    assert response.salary.mode == "FROM"
    assert response.salary.amount_rub == 150000
    assert response.level.grade == "JUNIOR"
    assert response.level.mode == "AT_LEAST"
    assert response.search_active is False


def test_soft_salary_and_ignored_grade_are_explicit_any_filters() -> None:
    user = _completed_user(
        cv_salary_amount=None,
        cv_salary_currency=None,
        filter_salary_mode=FilterMode.SOFT,
        cv_grade=None,
        filter_grade_mode=LevelFilterMode.IGNORE,
    )

    response = SearchProfileService.get_profile(user)

    assert response.salary.mode == "ANY"
    assert response.salary.amount_rub is None
    assert response.level.grade is None
    assert response.level.mode == "IGNORE"


@pytest.mark.parametrize(
    "user",
    [
        User.create(tg_id=1, cv_specializations_raw=["Frontend"]),
        _completed_user(cv_specializations_raw=[]),
        _completed_user(cv_salary_amount=None, filter_salary_mode=FilterMode.STRICT),
    ],
)
def test_incomplete_or_inconsistent_profile_is_rejected(user: User) -> None:
    with pytest.raises(IncompleteSearchProfileError):
        SearchProfileService.get_profile(user)


def test_inconsistent_grade_filter_is_rejected() -> None:
    user = _completed_user(cv_grade=None)
    user.filter_grade_mode = LevelFilterMode.AT_LEAST

    with pytest.raises(IncompleteSearchProfileError):
        SearchProfileService.get_profile(user)
