from types import TracebackType

import pytest

from app.application.services.user_service import UserService
from app.domain.shared import WorkFormat, WorkFormats
from app.domain.user.entities import User
from app.domain.user.value_objects import FilterMode, UserId


class _RepositoryFake:
    def __init__(self, user: User) -> None:
        self.user = user

    async def get_by_tg_id_for_update(self, tg_id: UserId) -> User | None:
        return self.user if self.user.tg_id == tg_id else None

    async def update(self, user: User) -> None:
        self.user = user


class _UnitOfWorkFake:
    def __init__(self, repository: _RepositoryFake) -> None:
        self.users = repository

    async def __aenter__(self) -> "_UnitOfWorkFake":
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


@pytest.mark.asyncio
async def test_legacy_user_service_writer_dual_writes_scalar_and_collection() -> None:
    repository = _RepositoryFake(User.create(tg_id=1))
    service = UserService(_UnitOfWorkFake(repository))  # type: ignore[arg-type]

    updated = await service.update_profile_work_format_filter(
        tg_id=1,
        work_format=WorkFormat.REMOTE,
        work_format_mode=FilterMode.STRICT,
    )

    assert updated is True
    assert repository.user.cv_work_format is WorkFormat.REMOTE
    assert repository.user.cv_work_formats == WorkFormats.from_values([WorkFormat.REMOTE])
