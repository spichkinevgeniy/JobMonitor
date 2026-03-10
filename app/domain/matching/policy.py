from app.domain.matching.entities import MatchDecision, MatchRejectionReason
from app.domain.shared.value_objects import WorkFormat
from app.domain.user.entities import User
from app.domain.user.value_objects import FilterMode
from app.domain.vacancy.entities import Vacancy


def evaluate_match(vacancy: Vacancy, user: User) -> MatchDecision:
    """Apply domain-level matching filters after repository prefilter."""
    if _rejected_by_salary(vacancy, user):
        return MatchDecision(accepted=False, reason=MatchRejectionReason.SALARY)

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


def _rejected_by_work_format(vacancy: Vacancy, user: User) -> bool:
    if user.filter_work_format_mode != FilterMode.STRICT:
        return False
    if user.cv_work_format is None:
        return False
    if vacancy.work_format == WorkFormat.UNDEFINED:
        return True

    return vacancy.work_format != user.cv_work_format
