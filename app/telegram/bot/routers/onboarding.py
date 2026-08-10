from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.application.services.user_service import UserService
from app.core.logger import get_app_logger
from app.core.privacy import user_ref
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
    logger.info("Started onboarding for user %s", user_ref(user_id))

    uow = UserUnitOfWork(async_session_factory)
    service = UserService(uow, build_observability_service())
    try:
        user, is_new = await service.get_or_create_user(
            tg_id=user_id,
            username=message.from_user.username,
        )
        logger.info("User %s saved in db", user_ref(user_id))
    except Exception:
        logger.exception("Failed to save user (user=%s)", user_ref(user_id))
        logger.info("/start aborted due to persistence failure")
        await state.clear()
        return

    await state.set_state(BotStates.main_menu)
    await message.answer(
        build_start_message(is_new=is_new),
        reply_markup=get_main_menu_kb(),
    )


@router.message(F.text == START_BUTTON_TEXT)
async def cmd_start_text(message: Message, state: FSMContext) -> None:
    await cmd_start(message, state)
