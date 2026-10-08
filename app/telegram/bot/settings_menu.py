from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup

from app.application.services.user_service import UserService
from app.domain.user.entities import User
from app.telegram.bot.keyboards import get_main_menu_kb, get_settings_menu_kb, get_start_kb
from app.telegram.bot.views import (
    build_settings_menu_text,
    build_settings_menu_view,
    build_settings_unavailable_text,
    build_start_required_text,
)
from app.telegram.bot.views.pulse import build_pulse_toggle_label


def build_settings_menu_markup(user: User) -> InlineKeyboardMarkup | None:
    """Клавиатура меню настроек или None, если мини-апп не настроен.

    Отдельно от отправки: переключатель сводки перерисовывает меню на месте.
    """
    view = build_settings_menu_view(user)
    if not all(
        [
            view.specialty_url,
            view.format_url,
            view.salary_url,
            view.level_url,
        ]
    ):
        return None

    return get_settings_menu_kb(
        specialty_and_skills_label=view.specialty_label,
        format_label=view.format_label,
        salary_label=view.salary_label,
        level_label=view.level_label,
        specialty_url=view.specialty_url,
        format_url=view.format_url,
        salary_url=view.salary_url,
        level_url=view.level_url,
        pulse_label=build_pulse_toggle_label(user.pulse_enabled),
    )


async def send_settings_menu(bot: Bot, chat_id: int, tg_id: int, users: UserService) -> None:
    user = await users.get_user_by_tg_id(tg_id)
    if user is None:
        await bot.send_message(
            chat_id=chat_id,
            text=build_start_required_text(),
            reply_markup=get_start_kb(),
        )
        return

    markup = build_settings_menu_markup(user)
    if markup is None:
        await bot.send_message(
            chat_id=chat_id,
            text=build_settings_unavailable_text(),
            reply_markup=get_main_menu_kb(),
        )
        return

    await bot.send_message(
        chat_id=chat_id,
        text=build_settings_menu_text(),
        reply_markup=markup,
    )
