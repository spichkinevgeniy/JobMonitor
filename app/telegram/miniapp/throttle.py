"""Кулдаун на выгрузку вакансий."""

import math
from datetime import UTC, datetime, timedelta

EXPORT_COOLDOWN = timedelta(seconds=60)
_MAX_TRACKED_USERS = 10_000

_last_export: dict[int, datetime] = {}


def seconds_until_export_allowed(tg_id: int) -> int:
    """0 — можно выгружать, иначе сколько секунд ждать."""
    last = _last_export.get(tg_id)
    if last is None:
        return 0

    elapsed = datetime.now(UTC) - last
    if elapsed >= EXPORT_COOLDOWN:
        return 0
    return max(1, math.ceil((EXPORT_COOLDOWN - elapsed).total_seconds()))


def register_export(tg_id: int) -> None:
    _prune()
    _last_export[tg_id] = datetime.now(UTC)


def _prune() -> None:
    if len(_last_export) < _MAX_TRACKED_USERS:
        return

    threshold = datetime.now(UTC) - EXPORT_COOLDOWN
    for key in [key for key, value in _last_export.items() if value < threshold]:
        del _last_export[key]
