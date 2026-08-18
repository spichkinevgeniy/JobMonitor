from app.domain.shared import SkillType, SpecializationType, WorkFormat, WorkFormats
from app.domain.user.entities import User
from app.domain.user.onboarding import (
    OnboardingDraft,
    OnboardingLevel,
    OnboardingSalaryMode,
    OnboardingStep,
    SalaryDraft,
    SpecialtyDraft,
)
from app.domain.user.value_objects import FilterMode
from app.infrastructure.db.mappers.user import user_from_model, user_to_model
from app.infrastructure.db.models import User as UserModel


def test_user_mapper_round_trip_preserves_skills() -> None:
    user = User.create(
        tg_id=123,
        username="alice",
        cv_specializations_raw=["Backend"],
        cv_skills_raw=["Python", "React"],
        filter_salary_mode=FilterMode.SOFT,
        filter_work_format_mode=FilterMode.SOFT,
    )

    model = user_to_model(user)
    restored = user_from_model(model)

    assert sorted(model.cv_skills) == ["Python", "React"]
    assert sorted(item.value for item in restored.cv_skills.items) == ["Python", "React"]


def test_user_mapper_normalizes_undefined_work_format_to_any() -> None:
    model = UserModel(
        tg_id=123,
        username="alice",
        cv_specializations=["Backend"],
        cv_skills=["Python"],
        cv_salary_amount=None,
        cv_salary_currency=None,
        filter_salary_mode=FilterMode.SOFT.value,
        cv_work_format=WorkFormat.UNDEFINED.value,
        filter_work_format_mode=FilterMode.STRICT.value,
        is_active=True,
    )

    restored = user_from_model(model)

    assert restored.cv_work_format is None
    assert restored.filter_work_format_mode == FilterMode.SOFT


def test_user_mapper_round_trip_preserves_multi_formats_and_onboarding_draft() -> None:
    draft = OnboardingDraft(
        current_step=OnboardingStep.LEVEL,
        max_visited_step=OnboardingStep.LEVEL,
        specialty=SpecialtyDraft(
            specializations=frozenset(
                {SpecializationType.UI_UX_DESIGN, SpecializationType.FRONTEND}
            ),
            skills=frozenset({SkillType.JAVASCRIPT, SkillType.DOCKER}),
        ),
        work_formats=WorkFormats.from_values([WorkFormat.REMOTE, WorkFormat.HYBRID]),
        salary=SalaryDraft(OnboardingSalaryMode.FROM, 150000),
        level=OnboardingLevel.JUNIOR_PLUS,
    )
    user = User.create(tg_id=123, onboarding_draft=draft)
    user.set_work_formats(WorkFormats.from_values([WorkFormat.REMOTE, WorkFormat.HYBRID]))

    model = user_to_model(user)
    restored = user_from_model(model)

    assert model.cv_work_formats == ["HYBRID", "REMOTE"]
    assert restored.cv_work_formats == user.cv_work_formats
    assert restored.onboarding_draft == draft
    assert model.onboarding_draft is not None
    assert model.onboarding_draft["schema_version"] == 2


def test_user_mapper_reads_legacy_single_specialty_onboarding_draft() -> None:
    model = UserModel(
        tg_id=123,
        cv_specializations=[],
        cv_skills=[],
        onboarding_draft={
            "schema_version": 1,
            "current_step": "SPECIALTY",
            "max_visited_step": "SPECIALTY",
            "data": {
                "specialty": {"specialty": "Backend", "skills": ["Python"]},
                "work_formats": None,
                "salary": None,
                "level": None,
            },
        },
    )

    restored = user_from_model(model)

    assert restored.onboarding_draft is not None
    assert restored.onboarding_draft.specialty is not None
    assert restored.onboarding_draft.specialty.specializations == frozenset(
        {SpecializationType.BACKEND}
    )


def test_user_mapper_dual_reads_legacy_scalar_when_collection_is_null() -> None:
    model = UserModel(
        tg_id=123,
        cv_specializations=[],
        cv_skills=[],
        cv_work_format=WorkFormat.REMOTE.value,
        filter_work_format_mode=FilterMode.STRICT.value,
        cv_work_formats=None,
    )

    restored = user_from_model(model)

    assert restored.cv_work_formats is None
    assert restored.effective_work_formats == WorkFormats.from_values([WorkFormat.REMOTE])
