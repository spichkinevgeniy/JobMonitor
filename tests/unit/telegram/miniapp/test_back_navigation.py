"""Возврат в аналитику со страницы настроек."""

import pytest
from fastapi.testclient import TestClient

from app.telegram.miniapp.app import build_miniapp_app


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(build_miniapp_app()) as instance:
        yield instance


def test_back_link_shown_when_came_from_stats(client: TestClient) -> None:
    page = client.get("/miniapp/specialty?from=stats").text

    assert "back-link" in page
    assert "/miniapp/stats" in page


def test_no_back_link_when_opened_directly(client: TestClient) -> None:
    """Из меню бота настройки открываются сами по себе — возврат там сбивает."""
    page = client.get("/miniapp/specialty").text

    assert "back-link" not in page


def test_stats_links_to_profile_with_marker(client: TestClient) -> None:
    page = client.get("/miniapp/stats").text

    assert "/miniapp/specialty?from=stats" in page
