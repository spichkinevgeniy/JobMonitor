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

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class User(Base):
    __tablename__ = "users"

    tg_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    cv_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    cv_specializations: Mapped[list[str]] = mapped_column(JSONB, default=list)
    cv_skills: Mapped[list[str]] = mapped_column(JSONB, default=list)

    cv_salary_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cv_salary_currency: Mapped[str | None] = mapped_column(String, nullable=True)
    filter_salary_mode: Mapped[str] = mapped_column(String, default="SOFT")

    cv_grade: Mapped[str | None] = mapped_column(String, nullable=True)
    filter_grade_mode: Mapped[str] = mapped_column(String, default="SOFT")

    cv_experience_level: Mapped[str | None] = mapped_column(String, nullable=True)
    filter_experience_mode: Mapped[str] = mapped_column(String, default="SOFT")

    cv_work_format: Mapped[str | None] = mapped_column(String, nullable=True)
    filter_work_format_mode: Mapped[str] = mapped_column(String, default="SOFT")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


async def init_db() -> None:
    from app.infrastructure.db.session import engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
