"""Кулдаун на выгрузку вакансий."""

from datetime import UTC, datetime, timedelta

import pytest

from app.telegram.miniapp import throttle
from app.telegram.miniapp.throttle import (
    EXPORT_COOLDOWN,
    register_export,
    seconds_until_export_allowed,
)

TG_ID = 777


@pytest.fixture(autouse=True)
def clean_state() -> None:
    throttle._last_export.clear()


def test_first_export_is_allowed() -> None:
    assert seconds_until_export_allowed(TG_ID) == 0


def test_second_export_right_after_is_blocked() -> None:
    register_export(TG_ID)

    retry_after = seconds_until_export_allowed(TG_ID)

    assert 0 < retry_after <= EXPORT_COOLDOWN.total_seconds()


def test_export_after_cooldown_is_allowed() -> None:
    throttle._last_export[TG_ID] = datetime.now(UTC) - EXPORT_COOLDOWN - timedelta(seconds=1)

    assert seconds_until_export_allowed(TG_ID) == 0


def test_retry_after_never_reports_zero() -> None:
    throttle._last_export[TG_ID] = datetime.now(UTC) - EXPORT_COOLDOWN + timedelta(milliseconds=1)

    assert seconds_until_export_allowed(TG_ID) >= 1


def test_users_do_not_block_each_other() -> None:
    register_export(TG_ID)

    assert seconds_until_export_allowed(TG_ID + 1) == 0


def test_stale_entries_are_pruned() -> None:
    stale = datetime.now(UTC) - EXPORT_COOLDOWN - timedelta(hours=1)
    throttle._last_export.update(dict.fromkeys(range(throttle._MAX_TRACKED_USERS), stale))

    register_export(TG_ID)

    assert throttle._last_export == {TG_ID: throttle._last_export[TG_ID]}
