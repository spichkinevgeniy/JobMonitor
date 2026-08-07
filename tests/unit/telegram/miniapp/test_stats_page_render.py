"""Разметка страницы аналитики: оба пустых состояния и ссылки на профиль."""

import pytest
from fastapi.testclient import TestClient

from app.telegram.miniapp.app import build_miniapp_app


@pytest.fixture(scope="module")
def page() -> str:
    with TestClient(build_miniapp_app()) as client:
        response = client.get("/miniapp/stats")

    assert response.status_code == 200
    return response.text


def test_renders_both_empty_states(page: str) -> None:
    assert "data-stats-empty" in page
    assert "data-stats-no-data" in page


def test_profile_url_is_substituted(page: str) -> None:
    assert 'data-profile-url="/miniapp/specialty"' in page
    assert 'href="/miniapp/specialty"' in page


def test_empty_states_start_hidden(page: str) -> None:
    """Показывает их JS после ответа API, иначе они мигнут при загрузке."""
    for marker in ("data-stats-empty", "data-stats-no-data", "data-stats-cards"):
        index = page.index(marker)
        assert "is-hidden" in page[index - 120 : index]
