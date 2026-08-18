from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(AsyncAttrs, DeclarativeBase):
    pass


class Vacancy(Base):
    __tablename__ = "vacancies"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    text: Mapped[str] = mapped_column(Text)

    specializations: Mapped[list[str]] = mapped_column(JSONB, default=list)
    skills: Mapped[list[str]] = mapped_column(JSONB, default=list)

    mirror_chat_id: Mapped[int] = mapped_column(BigInteger)
    mirror_message_id: Mapped[int] = mapped_column(BigInteger)

    content_hash: Mapped[str] = mapped_column(String, unique=True, index=True)

    salary_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_currency: Mapped[str | None] = mapped_column(String, nullable=True)

    grade: Mapped[str] = mapped_column(String, default="UNDEFINED")
    experience_level: Mapped[str] = mapped_column(String, default="UNDEFINED")
    work_format: Mapped[str] = mapped_column(String, default="UNDEFINED")
    company_type: Mapped[str] = mapped_column(String, default="UNDEFINED")

    source_channel: Mapped[str | None] = mapped_column(String, nullable=True)
    source_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    source_topic_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class User(Base):
    __tablename__ = "users"

    tg_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String, nullable=True)

    cv_specializations: Mapped[list[str]] = mapped_column(JSONB, default=list)
    cv_skills: Mapped[list[str]] = mapped_column(JSONB, default=list)

    cv_salary_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cv_salary_currency: Mapped[str | None] = mapped_column(String, nullable=True)
    filter_salary_mode: Mapped[str] = mapped_column(String, default="SOFT")

    cv_grade: Mapped[str | None] = mapped_column(String, nullable=True)
    filter_grade_mode: Mapped[str] = mapped_column(String, default="IGNORE")

    cv_experience_level: Mapped[str | None] = mapped_column(String, nullable=True)
    filter_experience_mode: Mapped[str] = mapped_column(String, default="IGNORE")

    cv_work_format: Mapped[str | None] = mapped_column(String, nullable=True)
    filter_work_format_mode: Mapped[str] = mapped_column(String, default="SOFT")
    cv_work_formats: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    onboarding_draft: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    onboarding_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class VacancyDispatchLog(Base):
    __tablename__ = "vacancy_dispatch_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_tg_id: Mapped[int] = mapped_column(BigInteger, index=True)
    vacancy_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    dispatched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    matched_skills: Mapped[list[str]] = mapped_column(JSONB, default=list)
    matched_specializations: Mapped[list[str]] = mapped_column(JSONB, default=list)
    feedback: Mapped[str | None] = mapped_column(String, nullable=True)
    feedback_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ResumeUploadLog(Base):
    """Лог загрузок резюме: по нему считаются кулдаун и дневная квота."""

    __tablename__ = "resume_upload_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_tg_id: Mapped[int] = mapped_column(BigInteger, index=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ResumeImportJob(Base):
    """Состояние разбора резюме для мини-аппа.

    Содержимое файла не хранится: он живёт в памяти на время задачи.
    Здесь только статус, чтобы фронт мог опрашивать результат.
    """

    __tablename__ = "resume_import_job"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_tg_id: Mapped[int] = mapped_column(BigInteger, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class MetricCounter(Base):
    """Счётчики событий, у которых нет своей таблицы.

    Хранится агрегат, а не событие: строк столько же, сколько пар
    «метрика + метка», и таблица не растёт от нагрузки.
    """

    __tablename__ = "metric_counter"

    name: Mapped[str] = mapped_column(String, primary_key=True)
    label: Mapped[str] = mapped_column(String, primary_key=True, default="")
    value: Mapped[int] = mapped_column(BigInteger, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


async def init_db() -> None:
    from app.infrastructure.db.session import engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
