from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.application.services.user_service import UserService
from app.core.config import config
from app.core.logger import get_app_logger
from app.infrastructure.db import UserUnitOfWork, async_session_factory
from app.infrastructure.observability import build_observability_service
from app.telegram.bot.keyboards import START_BUTTON_TEXT, get_main_menu_kb
from app.telegram.bot.states import BotStates
from app.telegram.bot.views import build_start_message

router = Router()
logger = get_app_logger(__name__)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        logger.warning("Received /start without from_user; skipping")
        await state.clear()
        return

    user_id = message.from_user.id
    logger.info(f"Started onboarding for user {user_id}")

    uow = UserUnitOfWork(async_session_factory)
    service = UserService(uow, build_observability_service())
    try:
        user, is_new = await service.get_or_create_user(
            tg_id=user_id,
            username=message.from_user.username,
        )
        logger.info(f"User {user.username} saved in db")
    except Exception:
        logger.exception(f"Failed to save user (tg_id={user_id})")
        logger.info("/start aborted due to persistence failure")
        await state.clear()
        return

    await state.set_state(BotStates.main_menu)
    await message.answer(
        build_start_message(is_new=is_new),
        reply_markup=get_main_menu_kb(),
    )
    if config.APP_ENV == "development" and user_id in config.DEV_TELEGRAM_IDS:
        from app.telegram.bot.routers.developer import build_developer_miniapp_keyboard

        onboarding_completed = user.onboarding_completed_at is not None
        keyboard = build_developer_miniapp_keyboard(onboarding_completed=onboarding_completed)
        if keyboard is not None:
            await message.answer(
                ("Dev: open Dashboard." if onboarding_completed else "Dev: open React onboarding."),
                reply_markup=keyboard,
            )


@router.message(F.text == START_BUTTON_TEXT)
async def cmd_start_text(message: Message, state: FSMContext) -> None:
    await cmd_start(message, state)
