"""Методы UserService, которые раньше жили прямо в обработчиках бота."""

from app.application.services.user_service import UserService
from app.domain.user.entities import User
from app.domain.user.value_objects import UserId


class FakeUsers:
    def __init__(self, *users: User) -> None:
        self._users = {user.tg_id.value: user for user in users}
        self.updated: list[int] = []

    async def get_by_tg_id(self, tg_id: UserId) -> User | None:
        return self._users.get(tg_id.value)

    async def update(self, user: User) -> None:
        self.updated.append(user.tg_id.value)

    async def list_active_tg_ids(self) -> list[int]:
        return [tg_id for tg_id, user in self._users.items() if user.is_active]


class FakeUow:
    def __init__(self, users: FakeUsers) -> None:
        self.users = users

    async def __aenter__(self) -> "FakeUow":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


def _service(*users: User) -> tuple[UserService, FakeUsers]:
    repo = FakeUsers(*users)
    return UserService(FakeUow(repo)), repo  # type: ignore[arg-type]


class TestDeactivate:
    """Кто заблокировал бота, тому рассылка дальше не идёт."""

    async def test_switches_user_off(self) -> None:
        user = User.create(tg_id=1)
        service, repo = _service(user)

        await service.deactivate(1)

        assert user.is_active is False
        assert repo.updated == [1]

    async def test_already_inactive_user_is_not_rewritten(self) -> None:
        service, repo = _service(User.create(tg_id=1, is_active=False))

        await service.deactivate(1)

        assert repo.updated == []

    async def test_unknown_user_is_ignored(self) -> None:
        service, repo = _service()

        await service.deactivate(1)

        assert repo.updated == []


class TestPulseSwitch:
    async def test_none_flips_the_setting(self) -> None:
        service, _ = _service(User.create(tg_id=1))

        states = []
        for _ in range(2):
            user = await service.set_pulse_enabled(1, None)
            assert user is not None
            states.append(user.pulse_enabled)

        assert states == [False, True]

    async def test_explicit_value_is_kept(self) -> None:
        """«Отписаться» дважды подряд не должно включить сводку обратно."""
        service, _ = _service(User.create(tg_id=1))

        await service.set_pulse_enabled(1, False)
        user = await service.set_pulse_enabled(1, False)

        assert user is not None and user.pulse_enabled is False

    async def test_unknown_user(self) -> None:
        service, _ = _service()

        assert await service.set_pulse_enabled(1, False) is None


async def test_lists_only_active_users() -> None:
    service, _ = _service(User.create(tg_id=1), User.create(tg_id=2, is_active=False))

    assert await service.list_active_tg_ids() == [1]
