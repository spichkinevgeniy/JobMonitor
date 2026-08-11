from datetime import UTC, datetime

from app.application.dto.miniapp.models import WorkFormatChoice
from app.application.dto.miniapp.onboarding import (
    LevelDraftRequest,
    OnboardingDraftRequest,
    OnboardingDraftResponse,
    OnboardingStateResponse,
    SalaryDraftRequest,
    SalaryDraftResponse,
    SpecialtyDraftRequest,
    WorkFormatDraftRequest,
)
from app.application.ports.unit_of_work import UserUnitOfWork
from app.domain.shared.value_objects import (
    CurrencyType,
    Grade,
    Salary,
    Skills,
    Specializations,
    WorkFormats,
)
from app.domain.user.entities import User
from app.domain.user.onboarding import (
    ONBOARDING_STEP_ORDER,
    OnboardingDraft,
    OnboardingLevel,
    OnboardingSalaryMode,
    OnboardingStep,
    SalaryDraft,
    SpecialtyDraft,
)
from app.domain.user.value_objects import FilterMode, LevelFilterMode, UserId


class OnboardingUserNotFoundError(Exception):
    pass


class InvalidOnboardingDraftError(Exception):
    pass


class OnboardingService:
    def __init__(self, uow: UserUnitOfWork) -> None:
        self._uow = uow

    async def get_state(self, tg_id: int) -> OnboardingStateResponse:
        async with self._uow:
            user = await self._uow.users.get_by_tg_id(UserId(tg_id))
            if user is None:
                raise OnboardingUserNotFoundError
            return self._state_response(user)

    async def save_draft(
        self,
        tg_id: int,
        request: OnboardingDraftRequest,
    ) -> OnboardingStateResponse:
        async with self._uow:
            user = await self._uow.users.get_by_tg_id_for_update(UserId(tg_id))
            if user is None:
                raise OnboardingUserNotFoundError

            draft = user.onboarding_draft or self._initial_draft(user)
            try:
                if request.step is not draft.current_step:
                    raise ValueError("Patch step must match current onboarding step")
                if request.data is None:
                    if (
                        ONBOARDING_STEP_ORDER[request.navigate_to]
                        >= ONBOARDING_STEP_ORDER[draft.current_step]
                    ):
                        raise ValueError("Navigation without step data is only allowed backward")
                    draft = draft.navigate(request.navigate_to)
                else:
                    draft = self._apply_patch(draft, request).navigate(request.navigate_to)
            except ValueError as exc:
                raise InvalidOnboardingDraftError(str(exc)) from exc
            user.onboarding_draft = draft
            await self._uow.users.update(user)
            return self._state_response(user)

    async def complete(self, tg_id: int) -> OnboardingStateResponse:
        async with self._uow:
            user = await self._uow.users.get_by_tg_id_for_update(UserId(tg_id))
            if user is None:
                raise OnboardingUserNotFoundError
            if user.onboarding_completed_at is not None and user.onboarding_draft is None:
                return self._state_response(user)

            draft = user.onboarding_draft
            if draft is None:
                raise InvalidOnboardingDraftError("Onboarding draft is incomplete")
            try:
                draft.validate_complete()
            except ValueError as exc:
                raise InvalidOnboardingDraftError(str(exc)) from exc

            self._apply_completed_draft(user, draft)
            user.onboarding_completed_at = user.onboarding_completed_at or datetime.now(UTC)
            user.onboarding_draft = None
            await self._uow.users.update(user)
            return self._state_response(user)

    @staticmethod
    def _apply_patch(
        draft: OnboardingDraft,
        request: OnboardingDraftRequest,
    ) -> OnboardingDraft:
        if isinstance(request, SpecialtyDraftRequest):
            assert request.data is not None
            return draft.with_specialty(
                SpecialtyDraft(
                    specializations=frozenset(request.data.specializations),
                    skills=frozenset(request.data.skills),
                )
            )
        if isinstance(request, WorkFormatDraftRequest):
            assert request.data is not None
            choices = [
                choice.value for choice in request.data.work_formats if choice.value != "ANY"
            ]
            return draft.with_work_formats(WorkFormats.from_strs(choices))
        if isinstance(request, SalaryDraftRequest):
            assert request.data is not None
            return draft.with_salary(
                SalaryDraft(mode=request.data.mode, amount_rub=request.data.amount_rub)
            )
        if isinstance(request, LevelDraftRequest):
            assert request.data is not None
            return draft.with_level(request.data.level)
        raise TypeError("Unsupported onboarding draft request")

    @staticmethod
    def _apply_completed_draft(user: User, draft: OnboardingDraft) -> None:
        draft.validate_complete()
        assert draft.specialty is not None
        assert draft.work_formats is not None
        assert draft.salary is not None
        assert draft.level is not None

        user.cv_specializations = Specializations.from_strs(
            [specialization.value for specialization in draft.specialty.specializations]
        )
        user.cv_skills = Skills.from_strs([skill.value for skill in draft.specialty.skills])
        user.set_work_formats(draft.work_formats)

        if draft.salary.mode is OnboardingSalaryMode.FROM:
            user.cv_salary = Salary.create(draft.salary.amount_rub, CurrencyType.RUB.value)
            user.filter_salary_mode = FilterMode.STRICT
        else:
            user.cv_salary = None
            user.filter_salary_mode = FilterMode.SOFT

        if draft.level is OnboardingLevel.JUNIOR_PLUS:
            user.cv_grade = Grade.JUNIOR
            user.filter_grade_mode = LevelFilterMode.AT_LEAST
        else:
            user.cv_grade = Grade(draft.level.value)
            user.filter_grade_mode = LevelFilterMode.EXACT

    @staticmethod
    def _initial_draft(user: User) -> OnboardingDraft:
        if user.onboarding_completed_at is None:
            return OnboardingDraft()
        return OnboardingService._draft_from_active_profile(user)

    @staticmethod
    def _draft_from_active_profile(user: User) -> OnboardingDraft:
        specialties = sorted(user.cv_specializations.items, key=lambda item: item.value)
        specialty = (
            SpecialtyDraft(
                specializations=frozenset(specialties),
                skills=frozenset(user.cv_skills.items),
            )
            if specialties
            else None
        )
        work_formats = user.effective_work_formats
        salary = (
            SalaryDraft(
                mode=OnboardingSalaryMode.FROM,
                amount_rub=user.cv_salary.amount,
            )
            if user.filter_salary_mode is FilterMode.STRICT
            and user.cv_salary is not None
            and user.cv_salary.amount is not None
            else SalaryDraft(mode=OnboardingSalaryMode.ANY)
        )
        level = OnboardingService._level_from_active_profile(user)
        return OnboardingDraft(
            current_step=OnboardingStep.SPECIALTY,
            max_visited_step=OnboardingStep.LEVEL,
            specialty=specialty,
            work_formats=work_formats,
            salary=salary,
            level=level,
        )

    @staticmethod
    def _level_from_active_profile(user: User) -> OnboardingLevel | None:
        if user.cv_grade is None:
            return None
        if user.cv_grade is Grade.JUNIOR and user.filter_grade_mode is LevelFilterMode.AT_LEAST:
            return OnboardingLevel.JUNIOR_PLUS
        try:
            return OnboardingLevel(user.cv_grade.value)
        except ValueError:
            return None

    @staticmethod
    def _state_response(user: User) -> OnboardingStateResponse:
        completed = user.onboarding_completed_at is not None
        draft = user.onboarding_draft
        if draft is None:
            draft = (
                OnboardingService._draft_from_active_profile(user)
                if completed
                else OnboardingDraft()
            )
        return OnboardingStateResponse(
            completed=completed,
            completed_at=user.onboarding_completed_at,
            current_step=draft.current_step,
            max_visited_step=draft.max_visited_step,
            draft=OnboardingService._draft_response(draft),
        )

    @staticmethod
    def _draft_response(draft: OnboardingDraft) -> OnboardingDraftResponse:
        work_formats: list[WorkFormatChoice] | None
        if draft.work_formats is None:
            work_formats = None
        elif not draft.work_formats.items:
            work_formats = [WorkFormatChoice.ANY]
        else:
            work_formats = sorted(
                (WorkFormatChoice(item.value) for item in draft.work_formats.items),
                key=lambda item: item.value,
            )
        specializations = (
            sorted(draft.specialty.specializations, key=lambda item: item.value)
            if draft.specialty
            else []
        )
        return OnboardingDraftResponse(
            specializations=specializations,
            specialty=specializations[0] if specializations else None,
            skills=sorted(draft.specialty.skills, key=lambda item: item.value)
            if draft.specialty
            else [],
            work_formats=work_formats,
            salary=SalaryDraftResponse(
                mode=draft.salary.mode,
                amount_rub=draft.salary.amount_rub,
            )
            if draft.salary
            else None,
            level=draft.level,
        )


__all__ = [
    "InvalidOnboardingDraftError",
    "OnboardingService",
    "OnboardingUserNotFoundError",
]
