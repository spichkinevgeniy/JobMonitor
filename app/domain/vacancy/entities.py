import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from app.domain.shared.value_objects import (
    PrimaryLanguages,
    Salary,
    Specializations,
    TechStack,
    WorkFormat,
)
from app.domain.vacancy.exceptions import ValidationError
from app.domain.vacancy.value_objects import ContentHash, VacancyId


@dataclass(slots=True)
class Vacancy:
    id: VacancyId
    text: str
    specializations: Specializations
    primary_languages: PrimaryLanguages
    tech_stack: TechStack
    min_experience_months: int

    mirror_chat_id: int
    mirror_message_id: int

    salary: Salary
    work_format: WorkFormat
    content_hash: ContentHash

    created_at: datetime
    is_active: bool = True

    @classmethod
    def create(
        cls,
        vacancy_id: UUID,
        text: str,
        specializations_raw: list[str],
        languages_raw: list[str],
        tech_stack_raw: list[str] | None,
        min_experience_months: int,
        mirror_chat_id: int,
        mirror_message_id: int,
        work_format: WorkFormat,
        salary_amount: int | None = None,
        salary_currency: str | None = None,
        created_at: datetime | None = None,
    ) -> "Vacancy":
        if not text or not text.strip():
            raise ValidationError("Текст вакансии не может быть пустым.")

        specs = Specializations.from_strs(specializations_raw)
        if not specs.items:
            raise ValidationError(
                "Вакансия должна содержать хотя бы одну специализацию для матчинга."
            )

        langs = PrimaryLanguages.from_strs(languages_raw)
        if not langs.items:
            raise ValidationError("Основные языки программирования не указаны. Матчинг невозможен.")

        stack = TechStack.create(tech_stack_raw)

        salary_vo = Salary.create(amount=salary_amount, currency=salary_currency)

        now = datetime.now(UTC)

        return cls(
            id=VacancyId(vacancy_id),
            text=text.strip(),
            specializations=specs,
            primary_languages=langs,
            tech_stack=stack,
            min_experience_months=max(0, min_experience_months),
            mirror_chat_id=mirror_chat_id,
            mirror_message_id=mirror_message_id,
            salary=salary_vo,
            work_format=work_format,
            content_hash=cls.compute_content_hash(text),
            created_at=created_at or now,
        )

    @staticmethod
    def compute_content_hash(raw_text: str) -> ContentHash:
        clean_text = "".join(raw_text.lower().split())
        clean_text = clean_text.replace("\x00", "")

        hash_val = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()
        return ContentHash(hash_val)

    def deactivate(self) -> None:
        self.is_active = False
