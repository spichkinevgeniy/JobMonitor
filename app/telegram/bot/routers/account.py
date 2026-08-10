from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from app.application.services.user_service import UserService
from app.core.logger import get_app_logger
from app.core.privacy import user_ref
from app.infrastructure.db import UserUnitOfWork, async_session_factory
from app.telegram.bot.keyboards import (
    DELETE_CANCEL_CALLBACK,
    DELETE_CONFIRM_CALLBACK,
    get_delete_confirm_kb,
)
from app.telegram.bot.views import (
    build_delete_cancelled_text,
    build_delete_confirm_text,
    build_delete_done_text,
    build_delete_keyboard_reset_text,
    build_delete_nothing_text,
)

router = Router()
logger = get_app_logger(__name__)


@router.message(Command("delete_me"))
async def cmd_delete_me(message: Message) -> None:
    await message.answer(build_delete_confirm_text(), reply_markup=get_delete_confirm_kb())


@router.callback_query(F.data == DELETE_CANCEL_CALLBACK)
async def cancel_delete(callback: CallbackQuery) -> None:
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(build_delete_cancelled_text())


@router.callback_query(F.data == DELETE_CONFIRM_CALLBACK)
async def confirm_delete(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        await callback.answer()
        return

    tg_id = callback.from_user.id
    service = UserService(UserUnitOfWork(async_session_factory))
    try:
        deleted = await service.delete_user(tg_id)
    except Exception:
        logger.exception("Failed to delete user data (user=%s)", user_ref(tg_id))
        await callback.answer("Не получилось удалить, попробуйте позже")
        return

    logger.info("User data deleted (user=%s, existed=%s)", user_ref(tg_id), deleted)
    await callback.answer()
    if not isinstance(callback.message, Message):
        return
    if not deleted:
        await callback.message.edit_text(build_delete_nothing_text())
        return

    await callback.message.edit_text(build_delete_done_text())
    # Клавиатура пережила бы удаление и предлагала кнопки несуществующему
    # профилю. Убираем её, вернётся после /start.
    await callback.message.answer(
        build_delete_keyboard_reset_text(), reply_markup=ReplyKeyboardRemove()
    )
