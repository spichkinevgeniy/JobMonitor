from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.ports.developer_user_data import IDeveloperUserDataRepository
from app.application.ports.unit_of_work import (
    DeveloperUserUnitOfWork as DeveloperUserUnitOfWorkPort,
)
from app.domain.user.repository import IUserRepository
from app.infrastructure.db.repositories.developer_user_data_repository import (
    DeveloperUserDataRepository,
)
from app.infrastructure.db.repositories.user_repository import UserRepository
from app.infrastructure.db.uow.base import SQLAlchemyUnitOfWork


class DeveloperUserUnitOfWork(SQLAlchemyUnitOfWork, DeveloperUserUnitOfWorkPort):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        super().__init__(session_factory)
        self._users: UserRepository | None = None
        self._developer_user_data: DeveloperUserDataRepository | None = None

    @property
    def users(self) -> IUserRepository:
        assert self._users is not None
        return self._users

    @property
    def developer_user_data(self) -> IDeveloperUserDataRepository:
        assert self._developer_user_data is not None
        return self._developer_user_data

    async def __aenter__(self) -> "DeveloperUserUnitOfWork":
        await super().__aenter__()
        assert self.session is not None
        self._users = UserRepository(self.session)
        self._developer_user_data = DeveloperUserDataRepository(self.session)
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
            self._developer_user_data = None


__all__ = ["DeveloperUserUnitOfWork"]
