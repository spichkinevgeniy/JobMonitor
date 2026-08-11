from datetime import UTC, datetime
from types import TracebackType

from app.application.services.developer_user_service import DeveloperUserService
from app.application.services.user_service import UserService
from app.domain.shared.value_objects import WorkFormat
from app.domain.user.entities import User
from app.domain.user.onboarding import OnboardingDraft
from app.domain.user.value_objects import FilterMode, UserId


class _UserRepositoryFake:
    def __init__(self, user: User | None) -> None:
        self.user = user

    async def get_by_tg_id(self, tg_id: UserId) -> User | None:
        return self.user if self.user is not None and self.user.tg_id == tg_id else None

    async def get_by_tg_id_for_update(self, tg_id: UserId) -> User | None:
        return await self.get_by_tg_id(tg_id)

    async def add(self, user: User) -> None:
        self.user = user

    async def update(self, user: User) -> None:
        self.user = user

    async def count_total(self) -> int:
        return int(self.user is not None)

    async def count_active(self) -> int:
        return int(self.user is not None and self.user.is_active)


class _DeveloperUserDataRepositoryFake:
    def __init__(self, users: _UserRepositoryFake) -> None:
        self._users = users
        self.dependent_records = 2

    async def delete_local_user_data(self, tg_id: UserId) -> None:
        assert self._users.user is not None
        assert self._users.user.tg_id == tg_id
        self.dependent_records = 0
        self._users.user = None


class _DeveloperUnitOfWorkFake:
    def __init__(self, users: _UserRepositoryFake) -> None:
        self.users = users
        self.developer_user_data = _DeveloperUserDataRepositoryFake(users)

    async def __aenter__(self) -> "_DeveloperUnitOfWorkFake":
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


class _UserUnitOfWorkFake:
    def __init__(self, users: _UserRepositoryFake) -> None:
        self.users = users

    async def __aenter__(self) -> "_UserUnitOfWorkFake":
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


async def test_reset_returns_existing_user_to_incomplete_onboarding() -> None:
    user = User.create(
        tg_id=123,
        username="ivan",
        cv_text="resume",
        cv_specializations_raw=["Frontend"],
        cv_skills_raw=["React"],
        cv_work_formats_raw=["REMOTE"],
        onboarding_draft=OnboardingDraft(),
        onboarding_completed_at=datetime.now(UTC),
        is_active=False,
    )
    user.set_legacy_work_format(WorkFormat.REMOTE, FilterMode.STRICT)
    users = _UserRepositoryFake(user)
    service = DeveloperUserService(_DeveloperUnitOfWorkFake(users))  # type: ignore[arg-type]

    assert await service.reset_profile(123) is True

    reset_user = users.user
    assert reset_user is not None
    assert reset_user.tg_id == UserId(123)
    assert reset_user.username == "ivan"
    assert reset_user.onboarding_completed_at is None
    assert reset_user.onboarding_draft is None
    assert reset_user.cv_text is None
    assert not reset_user.cv_specializations.items
    assert not reset_user.cv_skills.items
    assert not reset_user.effective_work_formats.items
    assert reset_user.is_active is True


async def test_delete_allows_normal_get_or_create_flow_to_create_user_again() -> None:
    users = _UserRepositoryFake(User.create(tg_id=123, username="old"))
    developer_uow = _DeveloperUnitOfWorkFake(users)
    developer_service = DeveloperUserService(developer_uow)  # type: ignore[arg-type]

    assert await developer_service.delete_user(123) is True
    assert users.user is None
    assert developer_uow.developer_user_data.dependent_records == 0

    user_service = UserService(_UserUnitOfWorkFake(users))  # type: ignore[arg-type]
    recreated, is_new = await user_service.get_or_create_user(123, "new")

    assert is_new is True
    assert recreated.tg_id == UserId(123)
    assert recreated.username == "new"
    assert users.user is recreated
