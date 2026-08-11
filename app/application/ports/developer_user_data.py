from typing import Protocol

from app.domain.user.value_objects import UserId


class IDeveloperUserDataRepository(Protocol):
    async def delete_local_user_data(self, tg_id: UserId) -> None: ...


__all__ = ["IDeveloperUserDataRepository"]
