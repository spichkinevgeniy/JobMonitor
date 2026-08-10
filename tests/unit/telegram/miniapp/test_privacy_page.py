"""Публичная страница политики и ссылка на неё из бота."""

import pytest
from fastapi.testclient import TestClient

from app.telegram.bot.views import build_privacy_text, build_privacy_url
from app.telegram.miniapp.app import build_miniapp_app


@pytest.fixture(scope="module")
def page() -> str:
    return TestClient(build_miniapp_app()).get("/privacy").text


class TestPage:
    def test_available_without_telegram_auth(self) -> None:
        """Политику должно быть видно и вне Telegram, иначе она бесполезна."""
        response = TestClient(build_miniapp_app()).get("/privacy")

        assert response.status_code == 200

    def test_all_placeholders_rendered(self, page: str) -> None:
        assert "{{" not in page

    @pytest.mark.parametrize(
        "claim",
        [
            "OpenRouter",  # передача резюме наружу
            "Нидерландах",  # где стоят серверы
            "/delete_me",  # как удалить данные
            "30 дней",  # срок ответа на запрос
        ],
    )
    def test_discloses_what_code_actually_does(self, page: str, claim: str) -> None:
        assert claim in page


class TestBotLink:
    def test_url_points_to_privacy(self) -> None:
        url = build_privacy_url()

        assert url == "" or url.endswith("/privacy")

    def test_text_survives_missing_base_url(self) -> None:
        """Без MINI_APP_BASE_URL ссылки нет, но ответ пользователю быть должен."""
        text = build_privacy_text("")

        assert text
        assert "http" not in text

    def test_text_mentions_deletion(self) -> None:
        assert "/delete_me" in build_privacy_text("https://example.com/privacy")
