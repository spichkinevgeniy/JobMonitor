from types import TracebackType
from typing import Protocol

from app.domain.user.repository import IUserRepository
from app.domain.vacancy.repository import IVacancyRepository


class UnitOfWork(Protocol):
    """Protocol for Unit of Work pattern implementation."""

    async def __aenter__(self) -> "UnitOfWork": ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


class VacancyUnitOfWork(UnitOfWork, Protocol):
    @property
    def vacancies(self) -> IVacancyRepository: ...


class UserUnitOfWork(UnitOfWork, Protocol):
    @property
    def users(self) -> IUserRepository: ...


class MatchingUnitOfWork(UnitOfWork, Protocol):
    @property
    def users(self) -> IUserRepository: ...

    @property
    def vacancies(self) -> IVacancyRepository: ...
