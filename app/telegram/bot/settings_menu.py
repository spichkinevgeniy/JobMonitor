from aiogram import Bot

from app.application.services.user_service import UserService
from app.infrastructure.db import UserUnitOfWork, async_session_factory
from app.telegram.bot.keyboards import get_main_menu_kb, get_settings_menu_kb, get_start_kb
from app.telegram.bot.views import (
    build_settings_menu_text,
    build_settings_menu_view,
    build_settings_unavailable_text,
    build_start_required_text,
)


async def send_settings_menu(bot: Bot, chat_id: int, tg_id: int) -> None:
    service = UserService(UserUnitOfWork(async_session_factory))
    user = await service.get_user_by_tg_id(tg_id)
    if user is None:
        await bot.send_message(
            chat_id=chat_id,
            text=build_start_required_text(),
            reply_markup=get_start_kb(),
        )
        return

    view = build_settings_menu_view(user)
    if not all(
        [
            view.specialty_url,
            view.format_url,
            view.salary_url,
            view.level_url,
        ]
    ):
        await bot.send_message(
            chat_id=chat_id,
            text=build_settings_unavailable_text(),
            reply_markup=get_main_menu_kb(),
        )
        return

    await bot.send_message(
        chat_id=chat_id,
        text=build_settings_menu_text(),
        reply_markup=get_settings_menu_kb(
            specialty_and_skills_label=view.specialty_label,
            format_label=view.format_label,
            salary_label=view.salary_label,
            level_label=view.level_label,
            specialty_url=view.specialty_url,
            format_url=view.format_url,
            salary_url=view.salary_url,
            level_url=view.level_url,
        ),
    )
