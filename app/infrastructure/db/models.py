from __future__ import annotations

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    func,
    true,
)
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

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    pulse_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())


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


class WeeklyPulseLog(Base):
    """Кому и за какую неделю уже ушла сводка.

    Каждая выкатка перезапускает контейнер, и без журнала рассылка после
    рестарта дошла бы до людей второй раз.
    """

    __tablename__ = "weekly_pulse_log"

    user_tg_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    week_start: Mapped[date] = mapped_column(Date, primary_key=True)
    status: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


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


class JevGateLog(Base):
    """Решения фильтра Jev перед Gemini.

    У отсеянных текстов (gate = skipped) ответа Gemini нет. Текст пишется
    только там, где его придётся читать: Jev и Gemini разошлись, Jev не
    уверена или строка попала в случайную выборку. У строк до включения
    фильтра gate пустой: это сравнение 26–28.09.2026.
    """

    __tablename__ = "jev_gate_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    text_length: Mapped[int] = mapped_column(Integer)
    jev_is_vacancy_p: Mapped[float | None] = mapped_column(Float, nullable=True)
    jev_grade: Mapped[str | None] = mapped_column(String(16), nullable=True)
    jev_grade_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    jev_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    jev_input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    jev_cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    jev_error: Mapped[str | None] = mapped_column(String(64), nullable=True)
    llm_is_vacancy: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    llm_grade: Mapped[str | None] = mapped_column(String(16), nullable=True)
    llm_error: Mapped[str | None] = mapped_column(String(64), nullable=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    text_reason: Mapped[str | None] = mapped_column(String(16), nullable=True)
    gate: Mapped[str | None] = mapped_column(String(16), nullable=True)
