import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from app.domain.shared.value_objects import (
    CompanyType,
    ExperienceLevel,
    Grade,
    Salary,
    Skills,
    Specializations,
    WorkFormat,
)
from app.domain.vacancy.exceptions import ValidationError
from app.domain.vacancy.value_objects import ContentHash, VacancyId


@dataclass(frozen=True, slots=True)
class DispatchedVacancy:
    """Вакансия вместе с моментом, когда бот отправил её пользователю."""

    vacancy: "Vacancy"
    dispatched_at: datetime


@dataclass(slots=True)
class Vacancy:
    id: VacancyId
    text: str
    specializations: Specializations
    skills: Skills

    mirror_chat_id: int
    mirror_message_id: int

    salary: Salary
    grade: Grade
    experience_level: ExperienceLevel
    work_format: WorkFormat
    content_hash: ContentHash

    created_at: datetime
    is_active: bool = True
    company_type: CompanyType = CompanyType.UNDEFINED
    source_channel: str | None = None
    source_message_id: int | None = None
    source_topic_id: int | None = None

    @property
    def source_url(self) -> str | None:
        """Ссылка на исходный пост. Строится только из публичного @username:
        у закрытых каналов такой ссылки не существует.

        В форумах (группах с темами) двухсоставная ссылка не открывает
        сообщение — нужна t.me/группа/тема/сообщение. Проверено на проде:
        t.me/front_end_jobs/16740 не открывается, t.me/front_end_jobs/2/16740
        открывается.
        """
        if not self.source_channel or not self.source_channel.startswith("@"):
            return None
        if self.source_message_id is None:
            return None

        chat = self.source_channel[1:]
        if self.source_topic_id is not None:
            return f"https://t.me/{chat}/{self.source_topic_id}/{self.source_message_id}"
        return f"https://t.me/{chat}/{self.source_message_id}"

    @classmethod
    def create(
        cls,
        vacancy_id: UUID,
        text: str,
        specializations_raw: list[str],
        skills_raw: list[str],
        mirror_chat_id: int,
        mirror_message_id: int,
        work_format: WorkFormat,
        grade: Grade = Grade.UNDEFINED,
        experience_level: ExperienceLevel = ExperienceLevel.UNDEFINED,
        salary_amount: int | None = None,
        salary_currency: str | None = None,
        created_at: datetime | None = None,
        company_type: CompanyType = CompanyType.UNDEFINED,
        source_channel: str | None = None,
        source_message_id: int | None = None,
        source_topic_id: int | None = None,
    ) -> "Vacancy":
        if not text or not text.strip():
            raise ValidationError("Vacancy text cannot be empty.")

        specs = Specializations.from_strs(specializations_raw)
        if not specs.items:
            raise ValidationError("Vacancy must contain at least one specialization for matching.")

        skills = Skills.from_strs(skills_raw)
        if not skills.items:
            raise ValidationError("Vacancy skills are missing. Matching cannot proceed.")

        salary_vo = Salary.create(amount=salary_amount, currency=salary_currency)
        now = datetime.now(UTC)

        return cls(
            id=VacancyId(vacancy_id),
            text=text.strip(),
            specializations=specs,
            skills=skills,
            mirror_chat_id=mirror_chat_id,
            mirror_message_id=mirror_message_id,
            salary=salary_vo,
            grade=grade,
            experience_level=experience_level,
            work_format=work_format,
            content_hash=cls.compute_content_hash(text),
            created_at=created_at or now,
            company_type=company_type,
            source_channel=source_channel,
            source_message_id=source_message_id,
            source_topic_id=source_topic_id,
        )

    @staticmethod
    def compute_content_hash(raw_text: str) -> ContentHash:
        clean_text = "".join(raw_text.lower().split())
        clean_text = clean_text.replace("\x00", "")

        hash_val = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()
        return ContentHash(hash_val)

    def deactivate(self) -> None:
        self.is_active = False
