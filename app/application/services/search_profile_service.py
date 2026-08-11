from app.application.dto.miniapp.models import (
    GradeChoice,
    LevelModeChoice,
    SalaryModeChoice,
    WorkFormatChoice,
)
from app.application.dto.miniapp.search_profile import (
    SearchProfileLevelResponse,
    SearchProfileResponse,
    SearchProfileSalaryResponse,
)
from app.domain.user.entities import User
from app.domain.user.value_objects import FilterMode, LevelFilterMode


class IncompleteSearchProfileError(Exception):
    pass


class SearchProfileService:
    @staticmethod
    def get_profile(user: User) -> SearchProfileResponse:
        if user.onboarding_completed_at is None:
            raise IncompleteSearchProfileError("Onboarding is not completed")

        specializations = sorted(user.cv_specializations.items, key=lambda item: item.value)
        if not specializations:
            raise IncompleteSearchProfileError("Search profile has no specialization")

        salary = SearchProfileService._salary_response(user)
        level = SearchProfileService._level_response(user)

        return SearchProfileResponse(
            specializations=specializations,
            skills=sorted(user.cv_skills.items, key=lambda item: item.value),
            work_formats=sorted(
                (WorkFormatChoice(item.value) for item in user.effective_work_formats.items),
                key=lambda item: item.value,
            ),
            salary=salary,
            level=level,
            search_active=user.is_active,
        )

    @staticmethod
    def _salary_response(user: User) -> SearchProfileSalaryResponse:
        if user.filter_salary_mode is not FilterMode.STRICT:
            return SearchProfileSalaryResponse(
                mode=SalaryModeChoice.ANY,
                amount_rub=None,
            )
        if user.cv_salary is None or user.cv_salary.amount is None:
            raise IncompleteSearchProfileError("Strict salary filter has no amount")
        return SearchProfileSalaryResponse(
            mode=SalaryModeChoice.FROM,
            amount_rub=user.cv_salary.amount,
        )

    @staticmethod
    def _level_response(user: User) -> SearchProfileLevelResponse:
        mode = LevelModeChoice(user.filter_grade_mode.value)
        if user.filter_grade_mode is LevelFilterMode.IGNORE:
            return SearchProfileLevelResponse(grade=None, mode=mode)
        if user.cv_grade is None:
            raise IncompleteSearchProfileError("Grade filter has no grade")
        return SearchProfileLevelResponse(
            grade=GradeChoice(user.cv_grade.value),
            mode=mode,
        )


__all__ = ["IncompleteSearchProfileError", "SearchProfileService"]
