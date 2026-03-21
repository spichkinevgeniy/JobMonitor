from __future__ import annotations

from collections.abc import Sequence


def normalize_chat_ref(chat: str | int) -> str | int:
    if isinstance(chat, int):
        return chat
    value = str(chat).strip()
    if value.startswith("https://"):
        value = value[len("https://") :]
    elif value.startswith("http://"):
        value = value[len("http://") :]
    if value.startswith("t.me/"):
        value = value[len("t.me/") :]
    if value.startswith(("@", "-100")):
        return value
    if value.lstrip("-").isdigit():
        return value
    return f"@{value}"


def normalized_channels(channels: Sequence[str | int]) -> list[str | int]:
    return [normalize_chat_ref(chat) for chat in channels]
