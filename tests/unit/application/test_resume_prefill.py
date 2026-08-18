"""Перенос разобранного резюме в черновик онбординга."""

from app.application.dto import OutResumeParse
from app.application.dto.resume_dto import SkillWithEvidence, SpecializationWithEvidence
from app.application.services.resume_prefill import build_prefill_draft
from app.domain.shared.value_objects import Grade, SkillType, SpecializationType, WorkFormat
from app.domain.user.onboarding import OnboardingDraft, OnboardingLevel, OnboardingSalaryMode


def _dto(**overrides: object) -> OutResumeParse:
    payload: dict[str, object] = {
        "is_resume": True,
        "specializations": [
            SpecializationWithEvidence(specialization=SpecializationType.BACKEND, evidence="x")
        ],
        "skills": [SkillWithEvidence(skill=SkillType.PYTHON, evidence="x")],
        "salary_amount": None,
        "salary_currency": None,
        "grade": Grade.MIDDLE,
        "work_format": WorkFormat.REMOTE,
    }
    payload.update(overrides)
    return OutResumeParse(**payload)  # type: ignore[arg-type]


def test_specializations_survive_as_a_set() -> None:
    """Резюме fullstack даёт две специализации, и обе должны дойти."""
    dto = _dto(
        specializations=[
            SpecializationWithEvidence(specialization=SpecializationType.BACKEND, evidence="x"),
            SpecializationWithEvidence(specialization=SpecializationType.FRONTEND, evidence="x"),
        ]
    )

    draft = build_prefill_draft(dto, OnboardingDraft())

    assert draft.specialty is not None
    assert draft.specialty.specializations == frozenset(
        {SpecializationType.BACKEND, SpecializationType.FRONTEND}
    )


def test_empty_specializations_leave_step_untouched() -> None:
    """Пустой шаг значит «не нашли», а не «пользователь ничего не выбрал»."""
    draft = build_prefill_draft(_dto(specializations=[]), OnboardingDraft())

    assert draft.specialty is None


def test_salary_fills_only_when_found() -> None:
    with_salary = build_prefill_draft(_dto(salary_amount=250000), OnboardingDraft())
    without = build_prefill_draft(_dto(salary_amount=None), OnboardingDraft())

    assert with_salary.salary is not None
    assert with_salary.salary.mode is OnboardingSalaryMode.FROM
    assert with_salary.salary.amount_rub == 250000
    assert without.salary is None


def test_undefined_work_format_is_not_a_choice() -> None:
    draft = build_prefill_draft(_dto(work_format=WorkFormat.UNDEFINED), OnboardingDraft())

    assert draft.work_formats is None


def test_grade_maps_to_level() -> None:
    draft = build_prefill_draft(_dto(grade=Grade.SENIOR), OnboardingDraft())

    assert draft.level is OnboardingLevel.SENIOR


def test_lead_has_no_onboarding_level() -> None:
    """В онбординге уровня Lead нет — выбор остаётся за пользователем."""
    draft = build_prefill_draft(_dto(grade=Grade.LEAD), OnboardingDraft())

    assert draft.level is None
