from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.ports.unit_of_work import VacancyUnitOfWork as VacancyUnitOfWorkPort
from app.domain.vacancy.repository import IVacancyRepository
from app.infrastructure.db.repositories.vacancy_repository import VacancyRepository
from app.infrastructure.db.uow.base import SQLAlchemyUnitOfWork


class VacancyUnitOfWork(SQLAlchemyUnitOfWork, VacancyUnitOfWorkPort):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        super().__init__(session_factory)
        self._vacancies: VacancyRepository | None = None

    @property
    def vacancies(self) -> IVacancyRepository:
        assert self._vacancies is not None
        return self._vacancies

    async def __aenter__(self) -> "VacancyUnitOfWork":
        await super().__aenter__()
        assert self.session is not None
        self._vacancies = VacancyRepository(self.session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        try:
            await super().__aexit__(exc_type, exc_val, exc_tb)
        finally:
            self._vacancies = None
