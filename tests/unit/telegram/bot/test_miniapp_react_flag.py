"""Переключатель между React-мини-аппом и легаси-страницами."""

import pytest

from app.core.config import config
from app.telegram.bot.views.settings import build_specialty_url, build_stats_url

BASE_URL = "https://example.test"


@pytest.fixture(autouse=True)
def base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "MINI_APP_BASE_URL", BASE_URL)


@pytest.fixture
def react(monkeypatch: pytest.MonkeyPatch):
    def _set(enabled: bool) -> None:
        monkeypatch.setattr(config, "MINIAPP_REACT_ENABLED", enabled)

    return _set


def test_disabled_by_default() -> None:
    """React не собирается в образ, поэтому по умолчанию ведём на легаси."""
    assert type(config).model_fields["MINIAPP_REACT_ENABLED"].default is False


def test_legacy_url_when_disabled(react) -> None:
    react(False)

    assert build_specialty_url() == f"{BASE_URL}/miniapp/specialty"


def test_react_url_when_enabled(react) -> None:
    react(True)

    assert build_specialty_url() == f"{BASE_URL}/miniapp/react/?mode=settings"


def test_no_stray_query_on_legacy(react) -> None:
    """mode=settings осмыслен только для React: на легаси это мусор в ссылке."""
    react(False)

    assert "mode=settings" not in build_specialty_url()


@pytest.mark.parametrize("enabled", [False, True])
def test_other_entries_stay_on_legacy(react, enabled: bool) -> None:
    """Флаг переключает только вход в настройки профиля."""
    react(enabled)

    assert build_stats_url() == f"{BASE_URL}/miniapp/stats"
