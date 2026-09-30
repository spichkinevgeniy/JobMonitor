"""Вакансии в настоящей базе: сохранение, поиск по хэшу, уникальность."""

from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.domain.shared import WorkFormat
from app.domain.vacancy.entities import Vacancy
from app.infrastructure.db import VacancyUnitOfWork, async_session_factory
from app.infrastructure.db.mappers.vacancy import vacancy_to_model
from app.infrastructure.db.models import Vacancy as VacancyModel

TEXT = "Ищем Senior Python-разработчика в платёжную команду. Удалённо, от 300 000 ₽. @hr"


def vacancy(text: str = TEXT, skills: tuple[str, ...] = ("Python", "SQL")) -> Vacancy:
    return Vacancy.create(
        vacancy_id=uuid4(),
        text=text,
        specializations_raw=["Backend"],
        skills_raw=list(skills),
        mirror_chat_id=-100,
        mirror_message_id=7,
        work_format=WorkFormat.REMOTE,
        salary_amount=300_000,
        salary_currency="RUB",
        source_channel="@jobs",
        source_message_id=5,
    )


async def save(item: Vacancy) -> None:
    uow = VacancyUnitOfWork(async_session_factory)
    async with uow:
        await uow.vacancies.upsert(item)


async def count_rows() -> int:
    async with async_session_factory() as session:
        return int(
            (await session.execute(select(func.count()).select_from(VacancyModel))).scalar_one()
        )


async def test_saved_vacancy_reads_back_intact() -> None:
    original = vacancy()
    await save(original)

    uow = VacancyUnitOfWork(async_session_factory)
    async with uow:
        loaded = await uow.vacancies.get_by_id(original.id)

    assert loaded is not None
    assert loaded.specializations == original.specializations
    assert loaded.skills == original.skills
    assert loaded.salary == original.salary
    assert loaded.work_format == original.work_format
    assert loaded.source_url == original.source_url


async def test_known_text_is_found_by_hash() -> None:
    original = vacancy()
    await save(original)

    uow = VacancyUnitOfWork(async_session_factory)
    async with uow:
        assert await uow.vacancies.exists_by_content_hash(original.content_hash)
        assert not await uow.vacancies.exists_by_content_hash(vacancy("Другой текст").content_hash)


async def test_same_text_updates_instead_of_adding() -> None:
    await save(vacancy(skills=("Python",)))
    await save(vacancy(skills=("Python", "Go")))

    assert await count_rows() == 1


async def test_database_refuses_second_row_with_same_text() -> None:
    """Защита от гонки: два одинаковых сообщения, проверенные одновременно."""
    async with async_session_factory() as first, async_session_factory() as second:
        first.add(vacancy_to_model(vacancy()))
        second.add(vacancy_to_model(vacancy()))
        await second.commit()

        with pytest.raises(IntegrityError):
            await first.commit()

    assert await count_rows() == 1
