from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.ports.unit_of_work import UserUnitOfWork as UserUnitOfWorkPort
from app.domain.user.repository import IUserRepository
from app.infrastructure.db.repositories.user_repository import UserRepository
from app.infrastructure.db.uow.base import SQLAlchemyUnitOfWork


class UserUnitOfWork(SQLAlchemyUnitOfWork, UserUnitOfWorkPort):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        super().__init__(session_factory)
        self._users: UserRepository | None = None

    @property
    def users(self) -> IUserRepository:
        assert self._users is not None
        return self._users

    async def __aenter__(self) -> "UserUnitOfWork":
        await super().__aenter__()
        assert self.session is not None
        self._users = UserRepository(self.session)
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
