"""Подтверждение разбора резюме.

Раньше бот заранее писал «если найдёт лишнее — настройте профиль», а что
именно извлеклось, человек не видел никогда. Отсюда профили с одним навыком
и с чужими специализациями, о которых владельцы не подозревали.
"""

from app.telegram.bot.keyboards import (
    RESUME_CONFIRM_BUTTON_TEXT,
    RESUME_CONFIRM_CALLBACK,
    RESUME_FIX_BUTTON_TEXT,
    get_resume_result_kb,
)
from app.telegram.bot.views import build_resume_result_text

URL = "https://example.test/miniapp/specialty"


class TestText:
    def test_shows_what_was_extracted(self) -> None:
        text = build_resume_result_text(["Frontend"], ["Vue", "TypeScript"])

        assert "Специализация: Frontend" in text
        assert "Навыки: Vue, TypeScript" in text

    def test_asks_to_confirm(self) -> None:
        assert build_resume_result_text(["Frontend"], ["Vue"]).endswith("Всё верно?")

    def test_says_when_nothing_found(self) -> None:
        """Пустой разбор — самый важный случай: человек должен это увидеть."""
        text = build_resume_result_text([], [])

        assert "Специализация: не нашёл" in text
        assert "Навыки: не нашёл" in text


class TestKeyboard:
    def test_both_buttons(self) -> None:
        buttons = [b for row in get_resume_result_kb(URL).inline_keyboard for b in row]

        assert [b.text for b in buttons] == [RESUME_CONFIRM_BUTTON_TEXT, RESUME_FIX_BUTTON_TEXT]

    def test_fix_opens_profile_settings(self) -> None:
        """Мини-апп, а не callback: иначе человек пойдёт искать настройки сам."""
        buttons = [b for row in get_resume_result_kb(URL).inline_keyboard for b in row]
        fix = [b for b in buttons if b.text == RESUME_FIX_BUTTON_TEXT][0]

        assert fix.web_app is not None
        assert fix.web_app.url == URL

    def test_confirm_is_a_callback(self) -> None:
        confirm = get_resume_result_kb(URL).inline_keyboard[0][0]

        assert confirm.callback_data == RESUME_CONFIRM_CALLBACK

    def test_survives_missing_mini_app_url(self) -> None:
        buttons = [b for row in get_resume_result_kb("").inline_keyboard for b in row]

        assert [b.text for b in buttons] == [RESUME_CONFIRM_BUTTON_TEXT]
