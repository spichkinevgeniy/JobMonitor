from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.core.config import config
from app.domain.user.entities import User
from app.telegram.bot.commands import DEVELOPER_COMMANDS, setup_bot_commands
from app.telegram.bot.routers import developer as developer_router_module
from app.telegram.bot.routers import get_developer_router
from app.telegram.bot.routers import onboarding as onboarding_router_module


def test_developer_router_is_unavailable_outside_development() -> None:
    assert get_developer_router("production") is None


async def test_developer_commands_are_not_registered_in_production(monkeypatch) -> None:
    monkeypatch.setattr(config, "APP_ENV", "production")
    monkeypatch.setattr(config, "DEV_TELEGRAM_USER_IDS", "123")
    bot = SimpleNamespace(set_my_commands=AsyncMock())

    await setup_bot_commands(bot)  # type: ignore[arg-type]

    bot.set_my_commands.assert_awaited_once()
    registered_commands = bot.set_my_commands.await_args.args[0]
    assert not {command.command for command in DEVELOPER_COMMANDS} & {
        command.command for command in registered_commands
    }


async def test_non_allowlisted_user_cannot_execute_reset(monkeypatch) -> None:
    monkeypatch.setattr(config, "APP_ENV", "development")
    monkeypatch.setattr(config, "DEV_TELEGRAM_USER_IDS", "123")
    service = SimpleNamespace(reset_profile=AsyncMock())
    monkeypatch.setattr(developer_router_module, "_build_service", lambda: service)
    message = SimpleNamespace(
        from_user=SimpleNamespace(id=456),
        answer=AsyncMock(),
    )
    state = SimpleNamespace(clear=AsyncMock())

    await developer_router_module.cmd_dev_reset_me(message, state)  # type: ignore[arg-type]

    service.reset_profile.assert_not_awaited()
    message.answer.assert_not_awaited()
    state.clear.assert_not_awaited()


async def test_non_allowlisted_user_cannot_execute_delete(monkeypatch) -> None:
    monkeypatch.setattr(config, "APP_ENV", "development")
    monkeypatch.setattr(config, "DEV_TELEGRAM_USER_IDS", "123")
    service = SimpleNamespace(delete_user=AsyncMock())
    monkeypatch.setattr(developer_router_module, "_build_service", lambda: service)
    message = SimpleNamespace(
        from_user=SimpleNamespace(id=456),
        answer=AsyncMock(),
    )
    state = SimpleNamespace(clear=AsyncMock())

    await developer_router_module.cmd_dev_delete_me(message, state)  # type: ignore[arg-type]

    service.delete_user.assert_not_awaited()
    message.answer.assert_not_awaited()
    state.clear.assert_not_awaited()


async def test_reset_response_opens_react_onboarding_from_current_tunnel(monkeypatch) -> None:
    monkeypatch.setattr(config, "APP_ENV", "development")
    monkeypatch.setattr(config, "DEV_TELEGRAM_USER_IDS", "123")
    monkeypatch.setattr(
        config,
        "MINI_APP_BASE_URL",
        "https://local-test.trycloudflare.com/",
    )
    service = SimpleNamespace(reset_profile=AsyncMock(return_value=True))
    monkeypatch.setattr(developer_router_module, "_build_service", lambda: service)
    message = SimpleNamespace(
        from_user=SimpleNamespace(id=123),
        answer=AsyncMock(),
    )
    state = SimpleNamespace(clear=AsyncMock())

    await developer_router_module.cmd_dev_reset_me(message, state)  # type: ignore[arg-type]

    state.clear.assert_awaited_once()
    message.answer.assert_awaited_once()
    reply_markup = message.answer.await_args.kwargs["reply_markup"]
    button = reply_markup.inline_keyboard[0][0]
    assert button.text == "Open React onboarding"
    assert button.web_app is not None
    assert (
        button.web_app.url == "https://local-test.trycloudflare.com/miniapp/react/?mode=onboarding"
    )


async def test_start_sends_react_onboarding_button_to_allowlisted_dev_user(monkeypatch) -> None:
    monkeypatch.setattr(config, "APP_ENV", "development")
    monkeypatch.setattr(config, "DEV_TELEGRAM_USER_IDS", "123")
    monkeypatch.setattr(
        config,
        "MINI_APP_BASE_URL",
        "https://local-test.trycloudflare.com",
    )
    service = SimpleNamespace(
        get_or_create_user=AsyncMock(return_value=(User.create(tg_id=123, username="ivan"), True))
    )
    monkeypatch.setattr(
        onboarding_router_module,
        "UserService",
        lambda *_args, **_kwargs: service,
    )
    monkeypatch.setattr(
        onboarding_router_module,
        "build_observability_service",
        lambda: None,
    )
    message = SimpleNamespace(
        from_user=SimpleNamespace(id=123, username="ivan"),
        answer=AsyncMock(),
    )
    state = SimpleNamespace(clear=AsyncMock(), set_state=AsyncMock())

    await onboarding_router_module.cmd_start(message, state)  # type: ignore[arg-type]

    assert message.answer.await_count == 2
    dev_reply = message.answer.await_args_list[1]
    assert dev_reply.args[0] == "Dev: open React onboarding."
    button = dev_reply.kwargs["reply_markup"].inline_keyboard[0][0]
    assert button.web_app.url.endswith("/miniapp/react/?mode=onboarding")


async def test_start_sends_dashboard_button_to_completed_allowlisted_dev_user(
    monkeypatch,
) -> None:
    monkeypatch.setattr(config, "APP_ENV", "development")
    monkeypatch.setattr(config, "DEV_TELEGRAM_USER_IDS", "123")
    monkeypatch.setattr(
        config,
        "MINI_APP_BASE_URL",
        "https://local-test.trycloudflare.com",
    )
    user = User.create(tg_id=123, username="ivan")
    user.onboarding_completed_at = datetime.now(UTC)
    service = SimpleNamespace(get_or_create_user=AsyncMock(return_value=(user, False)))
    monkeypatch.setattr(
        onboarding_router_module,
        "UserService",
        lambda *_args, **_kwargs: service,
    )
    monkeypatch.setattr(
        onboarding_router_module,
        "build_observability_service",
        lambda: None,
    )
    message = SimpleNamespace(
        from_user=SimpleNamespace(id=123, username="ivan"),
        answer=AsyncMock(),
    )
    state = SimpleNamespace(clear=AsyncMock(), set_state=AsyncMock())

    await onboarding_router_module.cmd_start(message, state)  # type: ignore[arg-type]

    dev_reply = message.answer.await_args_list[1]
    assert dev_reply.args[0] == "Dev: open Dashboard."
    button = dev_reply.kwargs["reply_markup"].inline_keyboard[0][0]
    assert button.text == "Open Dashboard"
    assert button.web_app.url.endswith("/miniapp/dashboard/")
