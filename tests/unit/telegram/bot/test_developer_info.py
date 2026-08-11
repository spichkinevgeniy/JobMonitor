"""Кто стоит за ботом: /developer_info из стандартной политики Telegram."""

from app.telegram.bot.views import build_developer_info_text

OPERATOR = "Евгений Спичкин"
EMAIL = "contact@example.com"
URL = "https://example.com/privacy"


def test_names_the_operator() -> None:
    assert OPERATOR in build_developer_info_text(OPERATOR, EMAIL, URL)


def test_gives_contact_outside_telegram() -> None:
    """Телеграм-канал связи исчезнет вместе с ботом, почта — нет."""
    assert EMAIL in build_developer_info_text(OPERATOR, EMAIL, URL)


def test_links_to_policy() -> None:
    assert URL in build_developer_info_text(OPERATOR, EMAIL, URL)


def test_survives_missing_policy_url() -> None:
    text = build_developer_info_text(OPERATOR, EMAIL, "")

    assert OPERATOR in text
    assert "http" not in text
