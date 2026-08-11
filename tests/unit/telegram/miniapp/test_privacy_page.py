"""Публичная страница политики и ссылка на неё из бота."""

import pytest
from fastapi.testclient import TestClient

from app.telegram.bot.views import build_privacy_text, build_privacy_url
from app.telegram.miniapp.app import build_miniapp_app


@pytest.fixture(scope="module")
def page() -> str:
    """Переносы строк в шаблоне не должны ломать поиск по фразам."""
    raw = TestClient(build_miniapp_app()).get("/privacy").text
    return " ".join(raw.split())


class TestPage:
    def test_available_without_telegram_auth(self) -> None:
        """Политику должно быть видно и вне Telegram, иначе она бесполезна."""
        response = TestClient(build_miniapp_app()).get("/privacy")

        assert response.status_code == 200

    def test_all_placeholders_rendered(self, page: str) -> None:
        assert "{{" not in page

    def test_has_contact_outside_telegram(self, page: str) -> None:
        """Единственный канал связи внутри Telegram исчезнет вместе с ботом."""
        assert "mailto:" in page

    @pytest.mark.parametrize(
        "claim",
        [
            "ИИ",  # резюме уходит внешнему сервису распознавания
            "Европейского союза",  # обработка за пределами России
            "/delete_me",  # как удалить данные
            "30 дней",  # срок ответа на запрос
        ],
    )
    def test_discloses_what_code_actually_does(self, page: str, claim: str) -> None:
        """Названия вендоров вынесены из политики, но сами факты передачи —
        внешнему ИИ и за границу — остаются: ради них политика и пишется."""
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
