"""Fallback в resume-роутере ловит любой текст, кроме явного списка, и стоит
раньше profile-роутера. Кнопка, забытая в этом списке, молча уходит в
«используйте кнопки меню» — здесь проверяется, что список полный.
"""

from app.telegram.bot.keyboards import MAIN_MENU_BUTTON_TEXTS, get_main_menu_kb


def test_every_menu_button_is_excluded_from_fallback() -> None:
    texts = {button.text for row in get_main_menu_kb().keyboard for button in row}

    assert texts <= MAIN_MENU_BUTTON_TEXTS


def test_exclusion_list_has_no_stale_entries() -> None:
    texts = {button.text for row in get_main_menu_kb().keyboard for button in row}

    assert MAIN_MENU_BUTTON_TEXTS <= texts
