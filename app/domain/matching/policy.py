from app.domain.matching.entities import MatchDecision, MatchRejectionReason
from app.domain.shared.value_objects import (
    EXPERIENCE_LEVEL_ORDER,
    GRADE_ORDER,
    ExperienceLevel,
    Grade,
    WorkFormat,
)
from app.domain.user.entities import User
from app.domain.user.value_objects import FilterMode, LevelFilterMode
from app.domain.vacancy.entities import Vacancy


def evaluate_match(vacancy: Vacancy, user: User) -> MatchDecision:
    """Apply domain-level matching filters after repository prefilter."""
    if _rejected_by_salary(vacancy, user):
        return MatchDecision(accepted=False, reason=MatchRejectionReason.SALARY)

    if _rejected_by_grade(vacancy, user):
        return MatchDecision(accepted=False, reason=MatchRejectionReason.GRADE)

    if _rejected_by_experience(vacancy, user):
        return MatchDecision(accepted=False, reason=MatchRejectionReason.EXPERIENCE)

    if _rejected_by_work_format(vacancy, user):
        return MatchDecision(accepted=False, reason=MatchRejectionReason.FORMAT)

    return MatchDecision(accepted=True)


def _rejected_by_salary(vacancy: Vacancy, user: User) -> bool:
    if user.filter_salary_mode != FilterMode.STRICT:
        return False
    if user.cv_salary is None or user.cv_salary.amount is None:
        return False
    if vacancy.salary.amount is None:
        return False

    return vacancy.salary.amount < user.cv_salary.amount


def _rejected_by_grade(vacancy: Vacancy, user: User) -> bool:
    if user.filter_grade_mode == LevelFilterMode.IGNORE:
        return False
    if user.cv_grade is None:
        return False
    if vacancy.grade == Grade.UNDEFINED:
        return False

    if user.filter_grade_mode == LevelFilterMode.EXACT:
        return vacancy.grade != user.cv_grade

    return GRADE_ORDER[vacancy.grade] > GRADE_ORDER[user.cv_grade]


def _rejected_by_experience(vacancy: Vacancy, user: User) -> bool:
    if user.filter_experience_mode == LevelFilterMode.IGNORE:
        return False
    if user.cv_experience_level is None:
        return False
    if vacancy.experience_level == ExperienceLevel.UNDEFINED:
        return False

    if user.filter_experience_mode == LevelFilterMode.EXACT:
        return vacancy.experience_level != user.cv_experience_level

    return (
        EXPERIENCE_LEVEL_ORDER[vacancy.experience_level]
        > EXPERIENCE_LEVEL_ORDER[user.cv_experience_level]
    )


def _rejected_by_work_format(vacancy: Vacancy, user: User) -> bool:
    if user.filter_work_format_mode != FilterMode.STRICT:
        return False
    if user.cv_work_format is None:
        return False
    if vacancy.work_format == WorkFormat.UNDEFINED:
        return True

    return vacancy.work_format != user.cv_work_format
