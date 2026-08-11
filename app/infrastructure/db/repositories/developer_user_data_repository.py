from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.developer_user_data import IDeveloperUserDataRepository
from app.domain.user.value_objects import UserId
from app.infrastructure.db.models import User as UserModel
from app.infrastructure.db.models import VacancyDispatchLog


class DeveloperUserDataRepository(IDeveloperUserDataRepository):
    """Persistence cleanup used exclusively by local developer tooling."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def delete_local_user_data(self, tg_id: UserId) -> None:
        await self._session.execute(
            delete(VacancyDispatchLog).where(VacancyDispatchLog.user_tg_id == tg_id.value)
        )
        await self._session.execute(delete(UserModel).where(UserModel.tg_id == tg_id.value))


__all__ = ["DeveloperUserDataRepository"]
