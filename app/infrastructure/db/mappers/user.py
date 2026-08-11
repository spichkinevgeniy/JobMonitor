from app.domain.shared.value_objects import ExperienceLevel as UserExperienceLevel
from app.domain.shared.value_objects import Grade as UserGrade
from app.domain.shared.value_objects import Salary as UserSalary
from app.domain.shared.value_objects import Skills as UserSkills
from app.domain.shared.value_objects import SkillType as UserSkillType
from app.domain.shared.value_objects import Specializations as UserSpecializations
from app.domain.shared.value_objects import SpecializationType as UserSpecializationType
from app.domain.shared.value_objects import WorkFormat as UserWorkFormat
from app.domain.shared.value_objects import WorkFormats as UserWorkFormats
from app.domain.user.entities import User
from app.domain.user.onboarding import (
    OnboardingDraft,
    OnboardingLevel,
    OnboardingSalaryMode,
    OnboardingStep,
    SalaryDraft,
    SpecialtyDraft,
)
from app.domain.user.value_objects import FilterMode, LevelFilterMode, UserId
from app.infrastructure.db.models import User as UserModel


def _parse_level_mode(raw: str | None) -> LevelFilterMode:
    if not raw:
        return LevelFilterMode.IGNORE

    normalized = raw.strip().upper()
    if not normalized:
        return LevelFilterMode.IGNORE
    if normalized == "SOFT":
        return LevelFilterMode.IGNORE
    if normalized == "STRICT":
        return LevelFilterMode.UP_TO
    return LevelFilterMode(normalized)


def user_to_model(user: User) -> UserModel:
    return UserModel(
        tg_id=user.tg_id.value,
        username=user.username,
        cv_specializations=[item.value for item in user.cv_specializations.items],
        cv_skills=[item.value for item in user.cv_skills.items],
        cv_salary_amount=user.cv_salary.amount if user.cv_salary else None,
        cv_salary_currency=(
            user.cv_salary.currency.value if user.cv_salary and user.cv_salary.currency else None
        ),
        filter_salary_mode=user.filter_salary_mode.value,
        cv_grade=user.cv_grade.value if user.cv_grade else None,
        filter_grade_mode=user.filter_grade_mode.value,
        cv_experience_level=user.cv_experience_level.value if user.cv_experience_level else None,
        filter_experience_mode=user.filter_experience_mode.value,
        cv_work_format=user.cv_work_format.value if user.cv_work_format else None,
        filter_work_format_mode=user.filter_work_format_mode.value,
        cv_work_formats=_work_formats_to_json(user.cv_work_formats),
        onboarding_draft=_onboarding_draft_to_json(user.onboarding_draft),
        onboarding_completed_at=user.onboarding_completed_at,
        is_active=user.is_active,
    )


def apply_user(model: UserModel, user: User) -> None:
    model.username = user.username
    model.cv_specializations = [item.value for item in user.cv_specializations.items]
    model.cv_skills = [item.value for item in user.cv_skills.items]
    model.cv_salary_amount = user.cv_salary.amount if user.cv_salary else None
    model.cv_salary_currency = (
        user.cv_salary.currency.value if user.cv_salary and user.cv_salary.currency else None
    )
    model.filter_salary_mode = user.filter_salary_mode.value
    model.cv_grade = user.cv_grade.value if user.cv_grade else None
    model.filter_grade_mode = user.filter_grade_mode.value
    model.cv_experience_level = user.cv_experience_level.value if user.cv_experience_level else None
    model.filter_experience_mode = user.filter_experience_mode.value
    model.cv_work_format = user.cv_work_format.value if user.cv_work_format else None
    model.filter_work_format_mode = user.filter_work_format_mode.value
    model.cv_work_formats = _work_formats_to_json(user.cv_work_formats)
    model.onboarding_draft = _onboarding_draft_to_json(user.onboarding_draft)
    model.onboarding_completed_at = user.onboarding_completed_at
    model.is_active = user.is_active


def user_from_model(model: UserModel) -> User:
    has_salary = model.cv_salary_amount is not None or bool(
        model.cv_salary_currency and model.cv_salary_currency.strip()
    )
    salary = (
        UserSalary.create(model.cv_salary_amount, model.cv_salary_currency) if has_salary else None
    )

    work_format = UserWorkFormat(model.cv_work_format) if model.cv_work_format else None
    if work_format == UserWorkFormat.UNDEFINED:
        work_format = None
    work_format_mode = (
        FilterMode(model.filter_work_format_mode)
        if model.filter_work_format_mode
        else FilterMode.SOFT
    )
    if work_format is None:
        work_format_mode = FilterMode.SOFT

    grade = UserGrade(model.cv_grade) if model.cv_grade else None
    if grade == UserGrade.UNDEFINED:
        grade = None
    grade_mode = _parse_level_mode(model.filter_grade_mode)
    if grade is None:
        grade_mode = LevelFilterMode.IGNORE

    experience_level = (
        UserExperienceLevel(model.cv_experience_level) if model.cv_experience_level else None
    )
    if experience_level == UserExperienceLevel.UNDEFINED:
        experience_level = None
    experience_mode = _parse_level_mode(model.filter_experience_mode)
    if experience_level is None:
        experience_mode = LevelFilterMode.IGNORE

    return User(
        tg_id=UserId(model.tg_id),
        username=model.username,
        cv_specializations=UserSpecializations.from_strs(model.cv_specializations or []),
        cv_skills=UserSkills.from_strs(model.cv_skills or []),
        cv_salary=salary,
        filter_salary_mode=(
            FilterMode(model.filter_salary_mode) if model.filter_salary_mode else FilterMode.SOFT
        ),
        cv_grade=grade,
        filter_grade_mode=grade_mode,
        cv_experience_level=experience_level,
        filter_experience_mode=experience_mode,
        cv_work_format=work_format,
        filter_work_format_mode=work_format_mode,
        cv_work_formats=(
            UserWorkFormats.from_strs(model.cv_work_formats)
            if model.cv_work_formats is not None
            else None
        ),
        onboarding_draft=_onboarding_draft_from_json(model.onboarding_draft),
        onboarding_completed_at=model.onboarding_completed_at,
        is_active=model.is_active,
    )


def _work_formats_to_json(work_formats: UserWorkFormats | None) -> list[str] | None:
    if work_formats is None:
        return None
    return sorted(item.value for item in work_formats.items)


def _onboarding_draft_to_json(draft: OnboardingDraft | None) -> dict[str, object] | None:
    if draft is None:
        return None
    return {
        "schema_version": 2,
        "current_step": draft.current_step.value,
        "max_visited_step": draft.max_visited_step.value,
        "data": {
            "specialty": (
                {
                    "specializations": sorted(
                        item.value for item in draft.specialty.specializations
                    ),
                    "skills": sorted(item.value for item in draft.specialty.skills),
                }
                if draft.specialty
                else None
            ),
            "work_formats": _work_formats_to_json(draft.work_formats),
            "salary": (
                {
                    "mode": draft.salary.mode.value,
                    "amount_rub": draft.salary.amount_rub,
                }
                if draft.salary
                else None
            ),
            "level": draft.level.value if draft.level else None,
        },
    }


def _onboarding_draft_from_json(payload: dict[str, object] | None) -> OnboardingDraft | None:
    if payload is None:
        return None
    schema_version = payload.get("schema_version")
    if schema_version not in {1, 2}:
        raise ValueError("Unsupported onboarding draft schema version")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise ValueError("Invalid onboarding draft data")

    specialty_payload = data.get("specialty")
    specialty: SpecialtyDraft | None = None
    if isinstance(specialty_payload, dict):
        raw_skills = specialty_payload.get("skills", [])
        if schema_version == 1:
            raw_specialty = specialty_payload.get("specialty")
            raw_specializations = [raw_specialty] if isinstance(raw_specialty, str) else None
        else:
            raw_specializations = specialty_payload.get("specializations")
        if not isinstance(raw_specializations, list) or not isinstance(raw_skills, list):
            raise ValueError("Invalid onboarding specialty draft")
        specialty = SpecialtyDraft(
            specializations=frozenset(
                UserSpecializationType(str(item)) for item in raw_specializations
            ),
            skills=frozenset(UserSkillType(str(item)) for item in raw_skills),
        )

    raw_work_formats = data.get("work_formats")
    work_formats = None
    if isinstance(raw_work_formats, list):
        work_formats = UserWorkFormats.from_strs([str(item) for item in raw_work_formats])

    salary_payload = data.get("salary")
    salary: SalaryDraft | None = None
    if isinstance(salary_payload, dict):
        raw_amount = salary_payload.get("amount_rub")
        if raw_amount is not None and not isinstance(raw_amount, int):
            raise ValueError("Invalid onboarding salary amount")
        salary = SalaryDraft(
            mode=OnboardingSalaryMode(str(salary_payload.get("mode"))),
            amount_rub=raw_amount,
        )

    raw_level = data.get("level")
    level = OnboardingLevel(raw_level) if isinstance(raw_level, str) else None
    return OnboardingDraft(
        current_step=OnboardingStep(str(payload.get("current_step"))),
        max_visited_step=OnboardingStep(str(payload.get("max_visited_step"))),
        specialty=specialty,
        work_formats=work_formats,
        salary=salary,
        level=level,
    )
