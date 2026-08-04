from pydantic import BaseModel, Field

from app.domain.shared.value_objects import (
    CompanyType,
    CurrencyType,
    ExperienceLevel,
    Grade,
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
    salary_amount: int | None = Field(
        default=None,
        description=(
            "Минимальная зарплата в RUB числом, без пробелов и знаков валюты. "
            "Если указан диапазон, бери минимальное значение. "
            "Если зарплата не указана или указана в другой валюте, верни null."
        ),
    )
    salary_currency: CurrencyType | None = Field(
        default=None,
        description="Валюта зарплаты: RUB или null.",
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
    company_type: CompanyType = Field(
        default=CompanyType.UNDEFINED,
        description=(
            "Тип компании-работодателя: PRODUCT, OUTSTAFF, STARTUP, PROJECT_WORK или UNDEFINED."
        ),
    )
