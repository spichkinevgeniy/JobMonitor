import json
from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel

from app.domain.shared.value_objects import ExperienceLevel, Grade, SkillType, SpecializationType
from app.domain.user.value_objects import LevelFilterMode


class WorkFormatChoice(StrEnum):
    ANY = "ANY"
    REMOTE = "REMOTE"
    HYBRID = "HYBRID"
    ONSITE = "ONSITE"


class SalaryModeChoice(StrEnum):
    ANY = "ANY"
    FROM = "FROM"


class GradeChoice(StrEnum):
    ANY = "ANY"
    INTERN = Grade.INTERN.value
    JUNIOR = Grade.JUNIOR.value
    MIDDLE = Grade.MIDDLE.value
    SENIOR = Grade.SENIOR.value
    LEAD = Grade.LEAD.value


class ExperienceLevelChoice(StrEnum):
    ANY = "ANY"
    NO_EXPERIENCE = ExperienceLevel.NO_EXPERIENCE.value
    ONE_TO_THREE_YEARS = ExperienceLevel.ONE_TO_THREE_YEARS.value
    THREE_TO_SIX_YEARS = ExperienceLevel.THREE_TO_SIX_YEARS.value
    SIX_PLUS_YEARS = ExperienceLevel.SIX_PLUS_YEARS.value


class LevelModeChoice(StrEnum):
    IGNORE = LevelFilterMode.IGNORE.value
    UP_TO = LevelFilterMode.UP_TO.value
    EXACT = LevelFilterMode.EXACT.value


@dataclass(frozen=True, slots=True)
class ChoiceOptionDto:
    value: str
    label: str


class SpecialtySaveRequest(BaseModel):
    init_data: str
    specializations: list[SpecializationType]
    skills: list[SkillType]


class FormatSaveRequest(BaseModel):
    init_data: str
    work_format_choice: WorkFormatChoice = WorkFormatChoice.ANY


class SalarySaveRequest(BaseModel):
    init_data: str
    salary_mode: SalaryModeChoice = SalaryModeChoice.ANY
    salary_amount_rub: int | None = None


class LevelSaveRequest(BaseModel):
    init_data: str
    grade_mode: LevelModeChoice = LevelModeChoice.IGNORE
    grade_choice: GradeChoice = GradeChoice.ANY
    experience_mode: LevelModeChoice = LevelModeChoice.IGNORE
    experience_level_choice: ExperienceLevelChoice = ExperienceLevelChoice.ANY


class SpecialtyReadResponse(BaseModel):
    specializations: list[str]
    skills: list[str]


class FormatReadResponse(BaseModel):
    work_format_choice: str


class SalaryReadResponse(BaseModel):
    salary_mode: str
    salary_amount_rub: int | None


class LevelReadResponse(BaseModel):
    grade_mode: str
    grade_choice: str
    experience_mode: str
    experience_level_choice: str


class SaveResponse(BaseModel):
    status: str = "ok"
    message: str


@dataclass(frozen=True, slots=True)
class MiniAppPayload:
    specializations: frozenset[SpecializationType]
    skills: frozenset[SkillType]
    work_format_choice: WorkFormatChoice
    salary_mode: SalaryModeChoice
    salary_amount_rub: int | None
    grade_mode: LevelModeChoice
    grade_choice: GradeChoice
    experience_mode: LevelModeChoice
    experience_level_choice: ExperienceLevelChoice


def parse_miniapp_payload(raw_payload: str) -> MiniAppPayload:
    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid mini-app payload") from exc

    if not isinstance(payload, dict):
        raise ValueError("Invalid mini-app payload")

    return MiniAppPayload(
        specializations=_parse_specializations(payload.get("specializations")),
        skills=_parse_skills(payload.get("skills")),
        work_format_choice=_parse_choice(payload.get("work_format_choice"), WorkFormatChoice),
        salary_mode=_parse_choice(payload.get("salary_mode"), SalaryModeChoice),
        salary_amount_rub=_parse_salary_amount(payload.get("salary_amount_rub")),
        grade_mode=_parse_choice(payload.get("grade_mode"), LevelModeChoice),
        grade_choice=_parse_choice(payload.get("grade_choice"), GradeChoice),
        experience_mode=_parse_choice(payload.get("experience_mode"), LevelModeChoice),
        experience_level_choice=_parse_choice(
            payload.get("experience_level_choice"),
            ExperienceLevelChoice,
        ),
    )


def _parse_specializations(raw_value: object) -> frozenset[SpecializationType]:
    return frozenset(_parse_enum_list(raw_value, SpecializationType))


def _parse_skills(raw_value: object) -> frozenset[SkillType]:
    return frozenset(_parse_enum_list(raw_value, SkillType))


def _parse_enum_list[EnumChoice: StrEnum](
    raw_value: object,
    enum_type: type[EnumChoice],
) -> list[EnumChoice]:
    if raw_value is None:
        return []
    if not isinstance(raw_value, list):
        raise ValueError("Invalid mini-app payload")

    items: list[EnumChoice] = []
    for item in raw_value:
        if not isinstance(item, str):
            raise ValueError("Invalid mini-app payload")
        try:
            items.append(enum_type(item.strip()))
        except ValueError:
            raise ValueError("Invalid mini-app payload") from None
    return items


def _parse_choice[EnumChoice: StrEnum](
    raw_value: object,
    enum_type: type[EnumChoice],
) -> EnumChoice:
    default_value = next(iter(enum_type))
    if raw_value is None:
        return default_value
    if not isinstance(raw_value, str):
        raise ValueError("Invalid mini-app payload")
    try:
        return enum_type(raw_value.strip())
    except ValueError as exc:
        raise ValueError("Invalid mini-app payload") from exc


def _parse_salary_amount(raw_value: object) -> int | None:
    if raw_value in (None, ""):
        return None
    if isinstance(raw_value, int):
        return raw_value if raw_value >= 0 else None
    if isinstance(raw_value, str) and raw_value.strip().isdigit():
        return int(raw_value.strip())
    raise ValueError("Invalid mini-app payload")
