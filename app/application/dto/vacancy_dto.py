from pydantic import BaseModel, Field

from app.domain.shared.value_objects import LanguageType, Salary, SpecializationType, WorkFormat


class InfoRawVacancy(BaseModel):
    text: str
    mirror_chat_id: int | None = None
    mirror_message_id: int | None = None
    chat_id: int | None = None
    message_id: int | None = None


class OutVacancyParse(BaseModel):
    is_vacancy: bool = Field(
        ...,
        description=("Признак того, является ли текст описанием вакансии (job description)."),
    )
    specializations: list[SpecializationType] = Field(
        default_factory=list,
        description="Области разработки. Если ищут фулстека — укажи [Backend, Frontend].",
    )
    primary_languages: list[LanguageType] = Field(
        default_factory=list,
        description="Основные языки программирования, требуемые в вакансии.",
    )
    min_experience_months: int = Field(
        default=0,
        description=(
            "Минимально требуемый опыт в месяцах. Если указано 'от 3 лет' -> 36. "
            "Если грейд 'Junior' без лет -> 12."
        ),
    )
    tech_stack: list[str] = Field(
        default_factory=list,
        description="Ключевые инструменты и фреймворки (Django, React, Kubernetes).",
    )
    salary: Salary | None = Field(
        default=None,
        description=(
            "Minimum salary. If a range is given, take the minimum. "
            "If salary is missing, set to null. If currency is missing, set currency to null."
        ),
    )
    work_format: WorkFormat = Field(
        default=WorkFormat.UNDEFINED,
        description="Формат работы (REMOTE, HYBRID, ONSITE, UNDEFINED).",
    )
