from dataclasses import dataclass, replace
from enum import StrEnum

from app.domain.shared.value_objects import (
    SkillType,
    SpecializationType,
    WorkFormats,
)


class OnboardingStep(StrEnum):
    SPECIALTY = "SPECIALTY"
    WORK_FORMAT = "WORK_FORMAT"
    SALARY = "SALARY"
    LEVEL = "LEVEL"


ONBOARDING_STEP_ORDER: dict[OnboardingStep, int] = {
    OnboardingStep.SPECIALTY: 1,
    OnboardingStep.WORK_FORMAT: 2,
    OnboardingStep.SALARY: 3,
    OnboardingStep.LEVEL: 4,
}


class OnboardingSalaryMode(StrEnum):
    ANY = "ANY"
    FROM = "FROM"


class OnboardingLevel(StrEnum):
    INTERN = "INTERN"
    JUNIOR = "JUNIOR"
    MIDDLE = "MIDDLE"
    SENIOR = "SENIOR"
    JUNIOR_PLUS = "JUNIOR_PLUS"


@dataclass(frozen=True, slots=True)
class SpecialtyDraft:
    specializations: frozenset[SpecializationType]
    skills: frozenset[SkillType]

    def __post_init__(self) -> None:
        if not self.specializations:
            raise ValueError("Choose at least one specialization")


@dataclass(frozen=True, slots=True)
class SalaryDraft:
    mode: OnboardingSalaryMode
    amount_rub: int | None = None

    def __post_init__(self) -> None:
        if self.mode is OnboardingSalaryMode.FROM:
            if self.amount_rub is None or self.amount_rub <= 0:
                raise ValueError("Salary amount must be greater than zero for FROM mode")
        elif self.amount_rub is not None:
            raise ValueError("Salary amount must be empty for ANY mode")


@dataclass(frozen=True, slots=True)
class OnboardingDraft:
    current_step: OnboardingStep = OnboardingStep.SPECIALTY
    max_visited_step: OnboardingStep = OnboardingStep.SPECIALTY
    specialty: SpecialtyDraft | None = None
    work_formats: WorkFormats | None = None
    salary: SalaryDraft | None = None
    level: OnboardingLevel | None = None

    def __post_init__(self) -> None:
        if ONBOARDING_STEP_ORDER[self.current_step] > ONBOARDING_STEP_ORDER[self.max_visited_step]:
            raise ValueError("Current onboarding step cannot exceed max visited step")

    def navigate(self, target: OnboardingStep) -> "OnboardingDraft":
        target_order = ONBOARDING_STEP_ORDER[target]
        max_order = ONBOARDING_STEP_ORDER[self.max_visited_step]
        if target_order > max_order + 1:
            raise ValueError("Cannot skip unvisited onboarding steps")
        max_visited = target if target_order > max_order else self.max_visited_step
        return replace(self, current_step=target, max_visited_step=max_visited)

    def with_specialty(self, value: SpecialtyDraft) -> "OnboardingDraft":
        return replace(self, specialty=value)

    def with_work_formats(self, value: WorkFormats) -> "OnboardingDraft":
        return replace(self, work_formats=value)

    def with_salary(self, value: SalaryDraft) -> "OnboardingDraft":
        return replace(self, salary=value)

    def with_level(self, value: OnboardingLevel) -> "OnboardingDraft":
        return replace(self, level=value)

    def validate_complete(self) -> None:
        if self.specialty is None:
            raise ValueError("Specialty step is incomplete")
        if self.work_formats is None:
            raise ValueError("Work format step is incomplete")
        if self.salary is None:
            raise ValueError("Salary step is incomplete")
        if self.level is None:
            raise ValueError("Level step is incomplete")


__all__ = [
    "ONBOARDING_STEP_ORDER",
    "OnboardingDraft",
    "OnboardingLevel",
    "OnboardingSalaryMode",
    "OnboardingStep",
    "SalaryDraft",
    "SpecialtyDraft",
]
