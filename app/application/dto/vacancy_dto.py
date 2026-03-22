from pydantic import BaseModel, Field

from app.domain.shared.value_objects import (
    ExperienceLevel,
    Grade,
    Salary,
    SkillType,
    SpecializationType,
    WorkFormat,
)


class InfoRawVacancy(BaseModel):
    text: str
    mirror_chat_id: int | None = None
    mirror_message_id: int | None = None
    chat_id: int | None = None
    message_id: int | None = None


class OutVacancyParse(BaseModel):
    is_vacancy: bool = Field(
        ...,
        description="Признак того, является ли текст описанием вакансии.",
    )
    specializations: list[SpecializationType] = Field(
        default_factory=list,
        description="Список специализаций, подходящих для вакансии.",
    )
    skills: list[SkillType] = Field(
        default_factory=list,
        description="Список ключевых скиллов из фиксированного перечня SkillType.",
    )
    salary: Salary | None = Field(
        default=None,
        description=(
            "Минимальная зарплата в RUB. Если указан диапазон, бери минимальное значение. "
            "Если зарплата не указана, указана в другой валюте или RUB нельзя надежно определить, верни null."
        ),
    )
    grade: Grade = Field(
        default=Grade.UNDEFINED,
        description="Уровень вакансии: INTERN, JUNIOR, MIDDLE, SENIOR, LEAD или UNDEFINED.",
    )
    experience_level: ExperienceLevel = Field(
        default=ExperienceLevel.UNDEFINED,
        description=(
            "Требуемый опыт: NO_EXPERIENCE, ONE_TO_THREE_YEARS, "
            "THREE_TO_SIX_YEARS, SIX_PLUS_YEARS или UNDEFINED."
        ),
    )
    work_format: WorkFormat = Field(
        default=WorkFormat.UNDEFINED,
        description="Формат работы: REMOTE, HYBRID, ONSITE или UNDEFINED.",
    )
