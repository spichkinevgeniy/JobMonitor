from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.types import Message

from app.application.services.user_service import UserService
from app.infrastructure.db import UserUnitOfWork, async_session_factory
from app.telegram.bot.keyboards import PROFILE_BUTTON_TEXT, get_start_kb
from app.telegram.bot.states import BotStates
from app.telegram.bot.views.profile import build_search_profile_text

router = Router()


@router.message(
    StateFilter(BotStates.main_menu, BotStates.processing_resume, None),
    F.text == PROFILE_BUTTON_TEXT,
)
async def show_profile(message: Message) -> None:
    if message.from_user is None:
        await message.answer(
            "Нажмите «Начать пользоваться ботом», чтобы продолжить.",
            reply_markup=get_start_kb(),
        )
        return

    service = UserService(UserUnitOfWork(async_session_factory))
    user = await service.get_user_by_tg_id(message.from_user.id)
    if user is None:
        await message.answer(
            "Нажмите «Начать пользоваться ботом», чтобы продолжить.",
            reply_markup=get_start_kb(),
        )
        return

    await message.answer(build_search_profile_text(user), parse_mode="HTML")
