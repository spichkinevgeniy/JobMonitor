"""Извлечение темы форума из события Telethon."""

from types import SimpleNamespace
from typing import Any

from app.telegram.scrapper.handlers import TelegramScraper


def _message(reply_to: Any) -> Any:
    return SimpleNamespace(reply_to=reply_to)


def test_topic_taken_from_top_id() -> None:
    reply = SimpleNamespace(forum_topic=True, reply_to_top_id=2, reply_to_msg_id=999)

    assert TelegramScraper._source_topic_id(_message(reply)) == 2


def test_falls_back_to_msg_id_at_topic_root() -> None:
    """Ответ прямо в начало темы: top_id пуст, тема — само сообщение."""
    reply = SimpleNamespace(forum_topic=True, reply_to_top_id=None, reply_to_msg_id=49)

    assert TelegramScraper._source_topic_id(_message(reply)) == 49


def test_plain_reply_is_not_a_topic() -> None:
    """Обычный ответ в группе — не форум, тему подставлять нельзя."""
    reply = SimpleNamespace(forum_topic=False, reply_to_top_id=None, reply_to_msg_id=17)

    assert TelegramScraper._source_topic_id(_message(reply)) is None


def test_no_reply_no_topic() -> None:
    assert TelegramScraper._source_topic_id(_message(None)) is None
