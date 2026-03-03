from typing import Protocol, runtime_checkable

from app.domain.user.entities import User
from app.domain.user.value_objects import UserId


@runtime_checkable
class IUserRepository(Protocol):
    async def get_by_tg_id(self, tg_id: UserId) -> User | None: ...

    async def add(self, user: User) -> None: ...

    async def update(self, user: User) -> None: ...

    async def upsert(self, user: User) -> None: ...

    async def find_prefiltered_candidates(
        self,
        specializations: set[str],
        primary_languages: set[str],
        is_active: bool = True,
    ) -> list[User]: ...
