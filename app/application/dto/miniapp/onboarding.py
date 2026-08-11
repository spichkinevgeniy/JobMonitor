from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.application.dto.miniapp.models import WorkFormatChoice
from app.domain.shared.value_objects import SkillType, SpecializationType
from app.domain.user.onboarding import (
    OnboardingLevel,
    OnboardingSalaryMode,
    OnboardingStep,
)


class SpecialtyDraftData(BaseModel):
    specializations: list[SpecializationType] = Field(min_length=1)
    skills: list[SkillType] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def accept_legacy_specialty(cls, value: Any) -> Any:
        if not isinstance(value, dict) or "specializations" in value:
            return value
        if "specialty" not in value:
            return value
        return {**value, "specializations": [value["specialty"]]}

    @model_validator(mode="after")
    def validate_specializations(self) -> "SpecialtyDraftData":
        if len(set(self.specializations)) != len(self.specializations):
            raise ValueError("Specializations must be unique")
        return self


class WorkFormatDraftData(BaseModel):
    work_formats: list[WorkFormatChoice]

    @model_validator(mode="after")
    def validate_choices(self) -> "WorkFormatDraftData":
        choices = self.work_formats
        if not choices:
            raise ValueError("Choose ANY or at least one work format")
        if len(set(choices)) != len(choices):
            raise ValueError("Work formats must be unique")
        if WorkFormatChoice.ANY in choices and len(choices) > 1:
            raise ValueError("ANY cannot be combined with concrete work formats")
        return self


class SalaryDraftData(BaseModel):
    mode: OnboardingSalaryMode
    amount_rub: int | None = None

    @model_validator(mode="after")
    def validate_salary(self) -> "SalaryDraftData":
        if self.mode is OnboardingSalaryMode.FROM:
            if self.amount_rub is None or self.amount_rub <= 0:
                raise ValueError("Salary amount must be greater than zero for FROM mode")
        elif self.amount_rub is not None:
            raise ValueError("Salary amount must be empty for ANY mode")
        return self


class LevelDraftData(BaseModel):
    level: OnboardingLevel


class SpecialtyDraftRequest(BaseModel):
    step: Literal[OnboardingStep.SPECIALTY]
    navigate_to: OnboardingStep
    data: SpecialtyDraftData | None


class WorkFormatDraftRequest(BaseModel):
    step: Literal[OnboardingStep.WORK_FORMAT]
    navigate_to: OnboardingStep
    data: WorkFormatDraftData | None


class SalaryDraftRequest(BaseModel):
    step: Literal[OnboardingStep.SALARY]
    navigate_to: OnboardingStep
    data: SalaryDraftData | None


class LevelDraftRequest(BaseModel):
    step: Literal[OnboardingStep.LEVEL]
    navigate_to: OnboardingStep
    data: LevelDraftData | None


type OnboardingDraftRequest = Annotated[
    SpecialtyDraftRequest | WorkFormatDraftRequest | SalaryDraftRequest | LevelDraftRequest,
    Field(discriminator="step"),
]


class SalaryDraftResponse(BaseModel):
    mode: OnboardingSalaryMode
    amount_rub: int | None


class OnboardingDraftResponse(BaseModel):
    specializations: list[SpecializationType]
    # Temporary response compatibility for already deployed singleton clients.
    specialty: SpecializationType | None
    skills: list[SkillType]
    work_formats: list[WorkFormatChoice] | None
    salary: SalaryDraftResponse | None
    level: OnboardingLevel | None


class OnboardingStateResponse(BaseModel):
    completed: bool
    completed_at: datetime | None
    current_step: OnboardingStep
    max_visited_step: OnboardingStep
    draft: OnboardingDraftResponse


__all__ = [
    "LevelDraftRequest",
    "OnboardingDraftRequest",
    "OnboardingDraftResponse",
    "OnboardingStateResponse",
    "SalaryDraftRequest",
    "SpecialtyDraftRequest",
    "WorkFormatDraftRequest",
]
