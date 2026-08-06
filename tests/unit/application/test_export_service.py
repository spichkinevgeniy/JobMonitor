"""Выгрузка вакансий: границы выборки."""

from types import TracebackType

from app.application.services.export_service import (
    MAX_EXPORT_VACANCIES,
    ExportFormat,
    ExportService,
)
from app.domain.vacancy.entities import DispatchedVacancy

TG_ID = 777


class FakeVacancyRepository:
    def __init__(self, dispatched: list[DispatchedVacancy]) -> None:
        self._dispatched = dispatched
        self.calls: list[int | None] = []

    async def find_dispatched_for_user(
        self, user_tg_id: int, limit: int | None = None
    ) -> list[DispatchedVacancy]:
        self.calls.append(limit)
        return self._dispatched[:limit] if limit is not None else self._dispatched


class FakeUnitOfWork:
    def __init__(self, dispatched: list[DispatchedVacancy] | None = None) -> None:
        self.vacancies = FakeVacancyRepository(dispatched or [])

    async def __aenter__(self) -> "FakeUnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None


async def test_build_limits_the_query() -> None:
    uow = FakeUnitOfWork()
    service = ExportService(uow)  # type: ignore[arg-type]

    await service.build(TG_ID, ExportFormat.JSON)

    assert uow.vacancies.calls == [MAX_EXPORT_VACANCIES]


async def test_build_returns_none_without_history() -> None:
    uow = FakeUnitOfWork()
    service = ExportService(uow)  # type: ignore[arg-type]

    assert await service.build(TG_ID, ExportFormat.JSON) is None
