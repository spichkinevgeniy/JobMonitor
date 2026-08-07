"""Аналитика в главном меню, а не только внутри профиля."""

import pytest

from app.telegram.bot import keyboards
from app.telegram.bot.keyboards import (
    HELP_BUTTON_TEXT,
    PROFILE_BUTTON_TEXT,
    PROFILE_STATS_BUTTON_TEXT,
    get_main_menu_kb,
)


def test_stats_button_goes_right_after_profile() -> None:
    rows = get_main_menu_kb().keyboard

    assert [button.text for button in rows[0]] == [
        PROFILE_BUTTON_TEXT,
        PROFILE_STATS_BUTTON_TEXT,
    ]


def test_stats_button_opens_the_mini_app() -> None:
    button = get_main_menu_kb().keyboard[0][1]

    assert button.web_app is not None
    assert button.web_app.url


def test_help_button_is_kept() -> None:
    rows = get_main_menu_kb().keyboard

    assert [button.text for button in rows[1]] == [HELP_BUTTON_TEXT]


def test_menu_survives_missing_mini_app_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Без базового URL мини-аппа кнопку не рисуем, а меню не ломаем."""
    monkeypatch.setattr(keyboards, "build_stats_url", lambda: "")

    rows = get_main_menu_kb().keyboard

    assert [button.text for row in rows for button in row] == [
        PROFILE_BUTTON_TEXT,
        HELP_BUTTON_TEXT,
    ]
