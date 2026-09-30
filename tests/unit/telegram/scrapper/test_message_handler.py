"""Обработчик скрапера: пересылает в зеркало и передаёт сообщение сервису."""

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest
from telethon.errors import ChatForwardsRestrictedError, MessageIdInvalidError

from app.application.dto import InfoRawVacancy
from app.application.ports.observability_port import SkipReason
from app.telegram.scrapper import handlers
from app.telegram.scrapper.handlers import MIN_VACANCY_TEXT_LENGTH, TelegramScraper

LONG_TEXT = "Ищем Python-разработчика. " * 10


class FakeMessages:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.processed: list[InfoRawVacancy] = []

    async def process(self, message: InfoRawVacancy) -> None:
        self.processed.append(message)
        if self.error is not None:
            raise self.error


class SkipSpy:
    def __init__(self) -> None:
        self.skipped: list[SkipReason] = []

    def observe_message_skipped(self, reason: SkipReason) -> None:
        self.skipped.append(reason)


def event(text: str) -> Any:
    return SimpleNamespace(
        chat_id=-200,
        chat=SimpleNamespace(username="jobs", title="Jobs"),
        message=SimpleNamespace(id=5, text=text, reply_to=None),
    )


def scraper(
    messages: FakeMessages, spy: SkipSpy, forward_error: Exception | None = None
) -> TelegramScraper:
    forward = AsyncMock(return_value=SimpleNamespace(chat_id=-100, id=7))
    if forward_error is not None:
        forward.side_effect = forward_error
    client = SimpleNamespace(forward_messages=forward)
    return TelegramScraper(client, messages, spy)  # type: ignore[arg-type]


class LogSpy:
    def __init__(self) -> None:
        self.levels: list[str] = []

    def warning(self, *args: Any, **kwargs: Any) -> None:
        self.levels.append("warning")

    def exception(self, *args: Any, **kwargs: Any) -> None:
        self.levels.append("error")


async def test_long_message_is_mirrored_and_handed_over() -> None:
    messages, spy = FakeMessages(), SkipSpy()

    await scraper(messages, spy)._message_handler(event(LONG_TEXT))

    assert len(messages.processed) == 1
    handed = messages.processed[0]
    assert (handed.mirror_chat_id, handed.mirror_message_id) == (-100, 7)
    assert handed.source_channel == "@jobs"
    assert spy.skipped == []


async def test_short_message_never_reaches_processing() -> None:
    messages, spy = FakeMessages(), SkipSpy()

    await scraper(messages, spy)._message_handler(event("x" * (MIN_VACANCY_TEXT_LENGTH - 1)))

    assert messages.processed == []
    assert spy.skipped == [SkipReason.TOO_SHORT]


async def test_failure_in_processing_is_counted_and_swallowed() -> None:
    """Упавшее сообщение не должно останавливать скрапер."""
    messages, spy = FakeMessages(error=RuntimeError("boom")), SkipSpy()

    await scraper(messages, spy)._message_handler(event(LONG_TEXT))

    assert spy.skipped == [SkipReason.PARSE_FAILED]


@pytest.mark.parametrize(
    ("error", "reason"),
    [
        (MessageIdInvalidError(request=None), SkipReason.SOURCE_UNAVAILABLE),
        (ChatForwardsRestrictedError(request=None), SkipReason.FORWARDS_RESTRICTED),
    ],
)
async def test_forward_refusal_is_a_quiet_skip(
    error: Exception, reason: SkipReason, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Удалённый пост и запрет пересылки — не сбой: без трейсбека, своя причина."""
    log = LogSpy()
    monkeypatch.setattr(handlers, "logger", log)
    messages, spy = FakeMessages(), SkipSpy()

    await scraper(messages, spy, forward_error=error)._message_handler(event(LONG_TEXT))

    assert messages.processed == []
    assert spy.skipped == [reason]
    assert log.levels == ["warning"]


async def test_unexpected_forward_failure_is_still_an_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    log = LogSpy()
    monkeypatch.setattr(handlers, "logger", log)
    messages, spy = FakeMessages(), SkipSpy()

    await scraper(messages, spy, forward_error=ConnectionError("down"))._message_handler(
        event(LONG_TEXT)
    )

    assert spy.skipped == [SkipReason.MIRROR_FAILED]
    assert log.levels == ["error"]
