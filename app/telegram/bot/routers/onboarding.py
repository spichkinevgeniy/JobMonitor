from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.application.services.user_service import UserService
from app.core.logger import get_app_logger
from app.infrastructure.db import UserUnitOfWork, async_session_factory
from app.telegram.bot.keyboards import START_BUTTON_TEXT, get_main_menu_kb
from app.telegram.bot.states import BotStates

router = Router()
logger = get_app_logger(__name__)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id if message.from_user else "unknown"
    logger.info(f"Started onboarding for user {user_id}")

    uow = UserUnitOfWork(async_session_factory)
    service = UserService(uow)
    try:
        user = await service.upsert_user(
            tg_id=message.from_user.id,
            username=message.from_user.username,
        )
        logger.info(f"User {user.username} saved in db")
    except Exception:
        logger.exception(f"Failed to save user (tg_id={message.from_user.id})")
        user = None

    body_text = (
        "Я помогу тебе следить за вакансиями, чтобы не пришлось вручную перебирать десятки "
        "каналов. Бот сам найдет подходящие посты и пришлет их тебе.\n\n"
        "С чего начать:\n"
        "• Загрузи резюме. Я посмотрю твой стек и специализацию, чтобы понимать, что именно искать.\n"
        "• Уточни фильтры. Настрой зарплату и формат работы, чтобы я не присылал лишнего.\n\n"
        "Теперь можно не отвлекаться на бесконечные уведомления из групп — я напишу только тогда, "
        "когда появится что-то, что тебе действительно подойдет. 💼\n\n"
        "Жми кнопку «📄 Загрузить новое резюме», и начнем."
    )

    if user is None:
        user_name = message.from_user.username or "друг"
    else:
        user_name = user.username or "друг"

    welcome_text = f"Привет, {user_name}! 👋\n\n{body_text}"
    await state.set_state(BotStates.main_menu)
    await message.answer(welcome_text, reply_markup=get_main_menu_kb())


@router.message(F.text == START_BUTTON_TEXT)
async def cmd_start_text(message: Message, state: FSMContext) -> None:
    await cmd_start(message, state)
