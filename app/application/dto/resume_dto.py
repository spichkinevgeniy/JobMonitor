from pydantic import BaseModel, Field

from app.domain.shared.value_objects import (
    CurrencyType,
    Salary,
    SkillType,
    SpecializationType,
    WorkFormat,
)


class OutResumeParse(BaseModel):
    is_resume: bool = Field(
        ...,
        description="Признак того, является ли документ резюме или профилем кандидата.",
    )
    full_relevant_text_from_resume: str | None = Field(
        default=None,
        description="Полный релевантный текст резюме. Если это не резюме, верни None.",
    )
    specializations: list[SpecializationType] = Field(
        default_factory=list,
        description="Список специализаций. Если кандидат fullstack, можно указать Backend и Frontend.",
    )
    skills: list[SkillType] = Field(
        default_factory=list,
        description="Список ключевых скиллов из фиксированного перечня SkillType.",
    )
    salary: Salary | None = Field(
        default=None,
        description=(
            "Желаемая зарплата в RUB. Если указан диапазон, бери минимальное значение. "
            "Если зарплата не указана, указана в другой валюте или RUB нельзя надежно определить, верни null."
        ),
    )
    work_format: WorkFormat = Field(
        default=WorkFormat.UNDEFINED,
        description="Формат работы: REMOTE, HYBRID, ONSITE или UNDEFINED.",
    )


class OutResumeSalaryParse(BaseModel):
    amount: int | None = Field(
        default=None,
        description=(
            "Желаемая сумма зарплаты. Если указан диапазон, бери минимальное значение. "
            "Если зарплата не указана, верни null."
        ),
    )
    currency: CurrencyType | None = Field(
        default=None,
        description="Валюта зарплаты: RUB или null.",
    )
    evidence: str | None = Field(
        default=None,
        description="Короткий фрагмент текста, подтверждающий найденную зарплату.",
    )
