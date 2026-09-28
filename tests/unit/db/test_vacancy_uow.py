"""Единица работы вакансий переводит ошибки базы на язык домена."""

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError

from app.domain.vacancy.exceptions import DuplicateVacancyError
from app.infrastructure.db.uow.vacancy_uow import VacancyUnitOfWork


class FakeSession:
    def __init__(self, error: Exception) -> None:
        self.error = error
        self.closed = False

    async def commit(self) -> None:
        raise self.error

    async def rollback(self) -> None:
        return None

    async def close(self) -> None:
        self.closed = True


async def test_uniqueness_violation_becomes_duplicate() -> None:
    session = FakeSession(IntegrityError("INSERT INTO vacancies", {}, Exception("duplicate key")))

    with pytest.raises(DuplicateVacancyError):
        async with VacancyUnitOfWork(lambda: session):  # type: ignore[arg-type,return-value]
            pass

    assert session.closed


async def test_other_database_errors_pass_through() -> None:
    """Дублем называется только нарушение уникальности, остальное — сбой."""
    session = FakeSession(OperationalError("SELECT 1", {}, Exception("connection lost")))

    with pytest.raises(OperationalError):
        async with VacancyUnitOfWork(lambda: session):  # type: ignore[arg-type,return-value]
            pass
