from dataclasses import dataclass

from fastapi import Request

from app.application.dto.miniapp import (
    ChoiceOptionDto,
    ExperienceLevelChoice,
    GradeChoice,
    WorkFormatChoice,
)
from app.domain.shared.value_objects import (
    ExperienceLevel,
    Grade,
    SkillType,
    SpecializationType,
    WorkFormat,
)


@dataclass(frozen=True, slots=True)
class SkillOptionView:
    value: str
    label: str
    section: SpecializationType


@dataclass(frozen=True, slots=True)
class SkillSectionView:
    title: str
    options: tuple[SkillOptionView, ...]


_SKILL_SECTION_ORDER = (
    SpecializationType.BACKEND,
    SpecializationType.FRONTEND,
    SpecializationType.DATA_SCIENCE_ML,
    SpecializationType.MOBILE,
    SpecializationType.GAMEDEV,
    SpecializationType.QA,
    SpecializationType.INFRASTRUCTURE_DEVOPS,
    SpecializationType.ANALYTICS,
)
_SKILL_OPTION_VIEWS: tuple[SkillOptionView, ...] = (
    SkillOptionView(SkillType.PYTHON.value, SkillType.PYTHON.value, SpecializationType.BACKEND),
    SkillOptionView(
        SkillType.JAVA_SCALA.value,
        SkillType.JAVA_SCALA.value,
        SpecializationType.BACKEND,
    ),
    SkillOptionView(SkillType.C_SHARP.value, SkillType.C_SHARP.value, SpecializationType.BACKEND),
    SkillOptionView(
        SkillType.C_PLUSPLUS.value,
        SkillType.C_PLUSPLUS.value,
        SpecializationType.BACKEND,
    ),
    SkillOptionView(SkillType.GO.value, SkillType.GO.value, SpecializationType.BACKEND),
    SkillOptionView(SkillType.C.value, SkillType.C.value, SpecializationType.BACKEND),
    SkillOptionView(SkillType.RUBY.value, SkillType.RUBY.value, SpecializationType.BACKEND),
    SkillOptionView(SkillType.PHP.value, SkillType.PHP.value, SpecializationType.BACKEND),
    SkillOptionView(
        SkillType.NODE_JS.value,
        SkillType.NODE_JS.value,
        SpecializationType.BACKEND,
    ),
    SkillOptionView(
        SkillType.TYPESCRIPT.value,
        SkillType.TYPESCRIPT.value,
        SpecializationType.BACKEND,
    ),
    SkillOptionView(
        SkillType.KOTLIN.value,
        SkillType.KOTLIN.value,
        SpecializationType.BACKEND,
    ),
    SkillOptionView(SkillType.REACT.value, SkillType.REACT.value, SpecializationType.FRONTEND),
    SkillOptionView(SkillType.VUE.value, SkillType.VUE.value, SpecializationType.FRONTEND),
    SkillOptionView(SkillType.ANGULAR.value, SkillType.ANGULAR.value, SpecializationType.FRONTEND),
    SkillOptionView(
        SkillType.MACHINE_LEARNING.value,
        SkillType.MACHINE_LEARNING.value,
        SpecializationType.DATA_SCIENCE_ML,
    ),
    SkillOptionView(SkillType.NLP.value, SkillType.NLP.value, SpecializationType.DATA_SCIENCE_ML),
    SkillOptionView(
        SkillType.COMPUTER_VISION.value,
        SkillType.COMPUTER_VISION.value,
        SpecializationType.DATA_SCIENCE_ML,
    ),
    SkillOptionView(
        SkillType.RECOMMENDER_SYSTEMS.value,
        SkillType.RECOMMENDER_SYSTEMS.value,
        SpecializationType.DATA_SCIENCE_ML,
    ),
    SkillOptionView(SkillType.IOS.value, SkillType.IOS.value, SpecializationType.MOBILE),
    SkillOptionView(SkillType.ANDROID.value, SkillType.ANDROID.value, SpecializationType.MOBILE),
    SkillOptionView(SkillType.FLUTTER.value, SkillType.FLUTTER.value, SpecializationType.MOBILE),
    SkillOptionView(
        SkillType.REACT_NATIVE.value,
        SkillType.REACT_NATIVE.value,
        SpecializationType.MOBILE,
    ),
    SkillOptionView(SkillType.UNITY.value, SkillType.UNITY.value, SpecializationType.GAMEDEV),
    SkillOptionView(
        SkillType.UNREAL_ENGINE.value,
        SkillType.UNREAL_ENGINE.value,
        SpecializationType.GAMEDEV,
    ),
    SkillOptionView(
        SkillType.GAMEPLAY_PROGRAMMING.value,
        SkillType.GAMEPLAY_PROGRAMMING.value,
        SpecializationType.GAMEDEV,
    ),
    SkillOptionView(
        SkillType.GRAPHICS.value,
        SkillType.GRAPHICS.value,
        SpecializationType.GAMEDEV,
    ),
    SkillOptionView(
        SkillType.MANUAL_QA.value,
        SkillType.MANUAL_QA.value,
        SpecializationType.QA,
    ),
    SkillOptionView(
        SkillType.QA_AUTOMATION.value,
        SkillType.QA_AUTOMATION.value,
        SpecializationType.QA,
    ),
    SkillOptionView(
        SkillType.PERFORMANCE_TESTING.value,
        SkillType.PERFORMANCE_TESTING.value,
        SpecializationType.QA,
    ),
    SkillOptionView(
        SkillType.DEVOPS.value,
        SkillType.DEVOPS.value,
        SpecializationType.INFRASTRUCTURE_DEVOPS,
    ),
    SkillOptionView(
        SkillType.SRE.value,
        SkillType.SRE.value,
        SpecializationType.INFRASTRUCTURE_DEVOPS,
    ),
    SkillOptionView(
        SkillType.DBA.value,
        SkillType.DBA.value,
        SpecializationType.INFRASTRUCTURE_DEVOPS,
    ),
    SkillOptionView(
        SkillType.SYSTEM_ADMINISTRATION.value,
        SkillType.SYSTEM_ADMINISTRATION.value,
        SpecializationType.INFRASTRUCTURE_DEVOPS,
    ),
    SkillOptionView(SkillType.SQL.value, SkillType.SQL.value, SpecializationType.ANALYTICS),
    SkillOptionView(
        SkillType.DATA_ANALYSIS.value,
        SkillType.DATA_ANALYSIS.value,
        SpecializationType.ANALYTICS,
    ),
)

_WORK_FORMAT_LABELS = {
    WorkFormatChoice.ANY.value: "Любой",
    WorkFormat.REMOTE.value: "Удаленка",
    WorkFormat.HYBRID.value: "Гибрид",
    WorkFormat.ONSITE.value: "Офис",
}
_GRADE_LABELS = {
    GradeChoice.ANY.value: "Любой",
    Grade.INTERN.value: "Intern",
    Grade.JUNIOR.value: "Junior",
    Grade.MIDDLE.value: "Middle",
    Grade.SENIOR.value: "Senior",
    Grade.LEAD.value: "Lead",
}
_EXPERIENCE_LEVEL_LABELS = {
    ExperienceLevelChoice.ANY.value: "Любой опыт",
    ExperienceLevel.NO_EXPERIENCE.value: "Без опыта",
    ExperienceLevel.ONE_TO_THREE_YEARS.value: "1-3 года",
    ExperienceLevel.THREE_TO_SIX_YEARS.value: "3-6 лет",
    ExperienceLevel.SIX_PLUS_YEARS.value: "6+ лет",
}
def _validate_skill_option_views() -> None:
    mapped_values = [item.value for item in _SKILL_OPTION_VIEWS]
    expected_values = [item.value for item in SkillType]

    if len(mapped_values) != len(set(mapped_values)):
        raise RuntimeError("Each SkillType must be mapped to exactly one mini-app UI section.")

    if set(mapped_values) != set(expected_values):
        raise RuntimeError("Mini-app skill UI sections must cover every SkillType exactly once.")

    unmapped_sections = {item.section for item in _SKILL_OPTION_VIEWS} - set(_SKILL_SECTION_ORDER)
    if unmapped_sections:
        raise RuntimeError("Mini-app skill UI sections must be declared in the section order.")


_validate_skill_option_views()


def build_specialization_options() -> list[str]:
    return [item.value for item in SpecializationType]


def build_skill_options() -> list[str]:
    return [item.value for item in SkillType]


def build_skill_sections() -> list[SkillSectionView]:
    return [
        SkillSectionView(
            title=section_title.value,
            options=tuple(item for item in _SKILL_OPTION_VIEWS if item.section == section_title),
        )
        for section_title in _SKILL_SECTION_ORDER
    ]


def build_work_format_options() -> list[ChoiceOptionDto]:
    options = [
        ChoiceOptionDto(
            value=WorkFormatChoice.ANY.value,
            label=_WORK_FORMAT_LABELS[WorkFormatChoice.ANY.value],
        )
    ]
    options.extend(
        ChoiceOptionDto(value=item.value, label=_WORK_FORMAT_LABELS[item.value])
        for item in WorkFormat
        if item is not WorkFormat.UNDEFINED
    )
    return options


def build_grade_options() -> list[ChoiceOptionDto]:
    options = [ChoiceOptionDto(value=GradeChoice.ANY.value, label=_GRADE_LABELS[GradeChoice.ANY.value])]
    options.extend(
        ChoiceOptionDto(value=item.value, label=_GRADE_LABELS[item.value])
        for item in Grade
        if item is not Grade.UNDEFINED
    )
    return options


def build_experience_level_options() -> list[ChoiceOptionDto]:
    options = [
        ChoiceOptionDto(
            value=ExperienceLevelChoice.ANY.value,
            label=_EXPERIENCE_LEVEL_LABELS[ExperienceLevelChoice.ANY.value],
        )
    ]
    options.extend(
        ChoiceOptionDto(value=item.value, label=_EXPERIENCE_LEVEL_LABELS[item.value])
        for item in ExperienceLevel
        if item is not ExperienceLevel.UNDEFINED
    )
    return options


def _path_for(request: Request, name: str, **path_params: object) -> str:
    return str(request.app.url_path_for(name, **path_params))


def build_specialty_page_context(request: Request) -> dict[str, object]:
    return {
        "page_title": "Настройка специальностей",
        "page_description": "Добавьте или удалите нужные:",
        "active_page": "specialty",
        "selected_specializations": [],
        "selected_skills": [],
        "specialization_options": build_specialization_options(),
        "skill_sections": build_skill_sections(),
        "action_label": "Сохранить",
        "save_url": _path_for(request, "miniapp-save-specialty"),
        "success_text": "Специализации и скиллы сохранены.",
    }


def build_format_page_context(request: Request) -> dict[str, object]:
    return {
        "page_title": "Настройка формата",
        "page_description": "Выберите подходящий формат работы.",
        "active_page": "format",
        "current_value": "",
        "options": build_work_format_options(),
        "action_label": "Сохранить",
        "save_url": _path_for(request, "miniapp-save-format"),
        "success_text": "Формат сохранен.",
    }


def build_salary_page_context(request: Request) -> dict[str, object]:
    return {
        "page_title": "Настройка зарплаты",
        "page_description": "Выберите режим зарплаты и укажите сумму при необходимости.",
        "active_page": "salary",
        "salary_mode": "",
        "salary_amount": "",
        "action_label": "Сохранить",
        "save_url": _path_for(request, "miniapp-save-salary"),
        "success_text": "Зарплата сохранена.",
    }


def build_level_page_context(request: Request) -> dict[str, object]:
    return {
        "page_title": "Грейд и опыт",
        "page_description": "Выберите ваш текущий уровень и подтвержденный опыт.",
        "active_page": "level",
        "grade_choice": "",
        "experience_level_choice": "",
        "grade_options": build_grade_options(),
        "experience_level_options": build_experience_level_options(),
        "action_label": "Сохранить",
        "save_url": _path_for(request, "miniapp-save-level"),
        "success_text": "Грейд и опыт сохранены.",
    }
