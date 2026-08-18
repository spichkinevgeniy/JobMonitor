from app.application.dto import OutResumeParse
from app.domain.shared.value_objects import Grade, WorkFormat, WorkFormats
from app.domain.user.onboarding import (
    OnboardingDraft,
    OnboardingLevel,
    OnboardingSalaryMode,
    SalaryDraft,
    SpecialtyDraft,
)


def build_prefill_draft(dto: OutResumeParse, current: OnboardingDraft) -> OnboardingDraft:
    """Заполняет черновик онбординга тем, что нашлось в резюме.

    Шаги, для которых в резюме ничего нет, остаются как были: пустое
    значение здесь — это «не нашли», а не «пользователь выбрал».
    """
    draft = current

    specializations = frozenset(item.specialization for item in dto.specializations)
    if specializations:
        draft = draft.with_specialty(
            SpecialtyDraft(
                specializations=specializations,
                skills=frozenset(item.skill for item in dto.skills),
            )
        )

    if dto.work_format is not None and dto.work_format is not WorkFormat.UNDEFINED:
        draft = draft.with_work_formats(WorkFormats.from_values([dto.work_format]))

    if dto.salary_amount is not None and dto.salary_amount > 0:
        draft = draft.with_salary(
            SalaryDraft(mode=OnboardingSalaryMode.FROM, amount_rub=dto.salary_amount)
        )

    level = _level_from_grade(dto.grade)
    if level is not None:
        draft = draft.with_level(level)

    return draft


def _level_from_grade(grade: Grade | None) -> OnboardingLevel | None:
    """У онбординга нет уровня Lead, поэтому такой грейд оставляем пользователю."""
    if grade is None or grade is Grade.UNDEFINED:
        return None
    try:
        return OnboardingLevel(grade.value)
    except ValueError:
        return None
