from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.ports.resume_import import IResumeImportJobRepository
from app.application.ports.unit_of_work import (
    ResumeImportUnitOfWork as ResumeImportUnitOfWorkPort,
)
from app.domain.user.repository import IUserRepository
from app.infrastructure.db.repositories.resume_import_job_repository import (
    ResumeImportJobRepository,
)
from app.infrastructure.db.repositories.user_repository import UserRepository
from app.infrastructure.db.uow.base import SQLAlchemyUnitOfWork


class ResumeImportUnitOfWork(SQLAlchemyUnitOfWork, ResumeImportUnitOfWorkPort):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        super().__init__(session_factory)
        self._users: UserRepository | None = None
        self._jobs: ResumeImportJobRepository | None = None

    @property
    def users(self) -> IUserRepository:
        assert self._users is not None
        return self._users

    @property
    def resume_import_jobs(self) -> IResumeImportJobRepository:
        assert self._jobs is not None
        return self._jobs

    async def __aenter__(self) -> "ResumeImportUnitOfWork":
        await super().__aenter__()
        assert self.session is not None
        self._users = UserRepository(self.session)
        self._jobs = ResumeImportJobRepository(self.session)
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
            self._users = None
            self._jobs = None
