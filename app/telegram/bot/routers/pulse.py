from datetime import UTC, datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.application.ports.observability_port import Feature
from app.application.services.weekly_pulse_service import WeeklyPulseService, last_full_week
from app.core.config import config
from app.domain.user.entities import User
from app.domain.user.value_objects import UserId
from app.infrastructure.db import UserUnitOfWork, VacancyUnitOfWork, async_session_factory
from app.infrastructure.observability import observe_feature
from app.telegram.bot.keyboards import (
    PULSE_OFF_CALLBACK,
    PULSE_SETTINGS_CALLBACK,
    PULSE_TOGGLE_CALLBACK,
    get_pulse_kb,
    get_start_kb,
)
from app.telegram.bot.settings_menu import build_settings_menu_markup, send_settings_menu
from app.telegram.bot.states import BotStates
from app.telegram.bot.views import build_start_required_text, build_stats_url
from app.telegram.bot.views.pulse import (
    build_pulse_preview_note,
    build_pulse_unsubscribed_text,
    build_weekly_pulse_text,
)

router = Router()


async def _set_pulse_enabled(tg_id: int, enabled: bool | None) -> User | None:
    """None переключает сводку на противоположное состояние."""
    async with UserUnitOfWork(async_session_factory) as uow:
        user = await uow.users.get_by_tg_id(UserId(tg_id))
        if user is None:
            return None
        user.pulse_enabled = not user.pulse_enabled if enabled is None else enabled
        await uow.users.update(user)
        return user


@router.callback_query(F.data == PULSE_OFF_CALLBACK)
async def unsubscribe_from_pulse(callback: CallbackQuery) -> None:
    await callback.answer()
    if await _set_pulse_enabled(callback.from_user.id, False) is None:
        return
    observe_feature(Feature.PULSE_UNSUBSCRIBE)
    if isinstance(callback.message, Message):
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(build_pulse_unsubscribed_text())


@router.callback_query(F.data == PULSE_SETTINGS_CALLBACK)
async def open_settings_from_pulse(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    bot = callback.bot
    if bot is None:
        return
    chat_id = callback.from_user.id
    if isinstance(callback.message, Message):
        chat_id = callback.message.chat.id
    await state.set_state(BotStates.main_menu)
    await send_settings_menu(bot, chat_id, callback.from_user.id)


@router.callback_query(F.data == PULSE_TOGGLE_CALLBACK)
async def toggle_pulse(callback: CallbackQuery) -> None:
    user = await _set_pulse_enabled(callback.from_user.id, None)
    if user is None:
        await callback.answer()
        return
    await callback.answer("Сводка включена" if user.pulse_enabled else "Сводка выключена")
    if not user.pulse_enabled:
        observe_feature(Feature.PULSE_UNSUBSCRIBE)
    markup = build_settings_menu_markup(user)
    if markup is not None and isinstance(callback.message, Message):
        await callback.message.edit_reply_markup(reply_markup=markup)


@router.message(Command("pulse_preview"))
async def pulse_preview(message: Message) -> None:
    """Сводка за прошлую неделю самому админу, мимо журнала и порога."""
    if message.from_user is None or message.from_user.id not in config.ADMIN_IDS:
        return

    async with UserUnitOfWork(async_session_factory) as uow:
        user = await uow.users.get_by_tg_id(UserId(message.from_user.id))
    if user is None:
        await message.answer(build_start_required_text(), reply_markup=get_start_kb())
        return

    week = last_full_week(datetime.now(UTC))
    pulse = await WeeklyPulseService(VacancyUnitOfWork(async_session_factory)).build(user, week)
    await message.answer(build_pulse_preview_note(pulse))
    await message.answer(
        build_weekly_pulse_text(pulse),
        reply_markup=get_pulse_kb(build_stats_url()),
    )
