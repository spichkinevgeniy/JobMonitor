"""Удаление данных по /delete_me."""

from typing import Any

import pytest

from app.telegram.bot.keyboards import (
    DELETE_CANCEL_CALLBACK,
    DELETE_CONFIRM_CALLBACK,
    get_delete_confirm_kb,
)
from app.telegram.bot.routers import account
from app.telegram.bot.views import (
    build_delete_cancelled_text,
    build_delete_done_text,
    build_delete_nothing_text,
)


class FakeMessage:
    def __init__(self) -> None:
        self.edited: list[str] = []
        self.answers: list[tuple[str, Any]] = []

    async def edit_text(self, text: str, **kwargs: Any) -> None:
        self.edited.append(text)

    async def answer(self, text: str, reply_markup: Any = None, **kwargs: Any) -> None:
        self.answers.append((text, reply_markup))


class FakeCallback:
    def __init__(self, message: Any, tg_id: int | None = 42) -> None:
        self.message = message
        self.from_user = None if tg_id is None else type("U", (), {"id": tg_id})()
        self.answered: list[str | None] = []

    async def answer(self, text: str | None = None, **kwargs: Any) -> None:
        self.answered.append(text)


class FakeService:
    def __init__(self, deleted: bool = True, raises: bool = False) -> None:
        self.deleted = deleted
        self.raises = raises
        self.calls: list[int] = []

    async def delete_user(self, tg_id: int) -> bool:
        self.calls.append(tg_id)
        if self.raises:
            raise RuntimeError("db down")
        return self.deleted


@pytest.fixture
def patch_service(monkeypatch: pytest.MonkeyPatch):
    def _install(service: FakeService) -> FakeService:
        monkeypatch.setattr(account, "UserService", lambda *a, **kw: service)
        monkeypatch.setattr(account, "UserUnitOfWork", lambda *a, **kw: None)
        # Хендлер отсеивает недоступные сообщения через isinstance, а собрать
        # настоящий aiogram Message ради этого дороже, чем подменить тип.
        monkeypatch.setattr(account, "Message", FakeMessage)
        return service

    return _install


class TestConfirmationKeyboard:
    def test_asks_before_deleting(self) -> None:
        """Удаление необратимо, поэтому одной команды мало."""
        callbacks = [
            b.callback_data for row in get_delete_confirm_kb().inline_keyboard for b in row
        ]

        assert DELETE_CONFIRM_CALLBACK in callbacks
        assert DELETE_CANCEL_CALLBACK in callbacks

    def test_cancel_goes_first(self) -> None:
        """Промах по необратимой кнопке дороже промаха по отмене."""
        buttons = [b for row in get_delete_confirm_kb().inline_keyboard for b in row]

        assert buttons[0].callback_data == DELETE_CANCEL_CALLBACK


class TestDeletion:
    @pytest.mark.asyncio
    async def test_cancel_does_not_touch_data(self, patch_service) -> None:
        service = patch_service(FakeService())
        message = FakeMessage()

        await account.cancel_delete(FakeCallback(message))

        assert service.calls == []
        assert message.edited == [build_delete_cancelled_text()]

    @pytest.mark.asyncio
    async def test_confirm_deletes_and_hides_keyboard(self, patch_service) -> None:
        patch_service(FakeService(deleted=True))
        message = FakeMessage()

        await account.confirm_delete(FakeCallback(message, tg_id=777))

        assert message.edited == [build_delete_done_text()]
        assert len(message.answers) == 1
        assert message.answers[0][1] is not None

    @pytest.mark.asyncio
    async def test_confirm_passes_the_caller_id(self, patch_service) -> None:
        """Удалять можно только себя: id берётся из callback, не из текста."""
        service = patch_service(FakeService())

        await account.confirm_delete(FakeCallback(FakeMessage(), tg_id=777))

        assert service.calls == [777]

    @pytest.mark.asyncio
    async def test_nothing_to_delete(self, patch_service) -> None:
        patch_service(FakeService(deleted=False))
        message = FakeMessage()

        await account.confirm_delete(FakeCallback(message))

        assert message.edited == [build_delete_nothing_text()]
        assert message.answers == []

    @pytest.mark.asyncio
    async def test_failure_does_not_claim_success(self, patch_service) -> None:
        patch_service(FakeService(raises=True))
        message = FakeMessage()
        callback = FakeCallback(message)

        await account.confirm_delete(callback)

        assert message.edited == []
        assert callback.answered and callback.answered[0] is not None

    @pytest.mark.asyncio
    async def test_without_user_context(self, patch_service) -> None:
        service = patch_service(FakeService())

        await account.confirm_delete(FakeCallback(FakeMessage(), tg_id=None))

        assert service.calls == []


def test_deletion_covers_every_table_holding_tg_id() -> None:
    """Новая таблица с tg_id должна попадать в удаление вместе с остальными.

    Внешних ключей нет, каскад не сработает: список в репозитории — это
    единственное, что связывает таблицы с удалением профиля.
    """
    import inspect

    from app.infrastructure.db import models
    from app.infrastructure.db.repositories.user_repository import UserRepository

    with_tg_id = {
        name
        for name, obj in vars(models).items()
        if inspect.isclass(obj) and hasattr(obj, "user_tg_id")
    }
    source = inspect.getsource(UserRepository.delete_by_tg_id)
    missing = {name for name in with_tg_id if name not in source}

    assert not missing, f"не удаляются: {sorted(missing)}"
