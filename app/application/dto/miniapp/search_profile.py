from pydantic import BaseModel

from app.application.dto.miniapp.models import (
    GradeChoice,
    LevelModeChoice,
    SalaryModeChoice,
    WorkFormatChoice,
)
from app.domain.shared.value_objects import SkillType, SpecializationType


class SearchProfileSalaryResponse(BaseModel):
    mode: SalaryModeChoice
    amount_rub: int | None


class SearchProfileLevelResponse(BaseModel):
    grade: GradeChoice | None
    mode: LevelModeChoice


class SearchProfileResponse(BaseModel):
    specializations: list[SpecializationType]
    skills: list[SkillType]
    work_formats: list[WorkFormatChoice]
    salary: SearchProfileSalaryResponse
    level: SearchProfileLevelResponse
    search_active: bool


__all__ = [
    "SearchProfileLevelResponse",
    "SearchProfileResponse",
    "SearchProfileSalaryResponse",
]
