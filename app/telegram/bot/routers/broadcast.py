import asyncio

from aiogram import Router
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from app.core.config import config
from app.core.logger import get_app_logger
from app.domain.user.value_objects import UserId
from app.infrastructure.db import UserUnitOfWork, async_session_factory

router = Router()
logger = get_app_logger(__name__)

SEND_DELAY_SECONDS = 0.05


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, command: CommandObject) -> None:
    if message.from_user is None or message.from_user.id not in config.ADMIN_IDS:
        return

    text = command.args
    if not text:
        await message.answer("Использование: /broadcast <текст сообщения>")
        return

    bot = message.bot
    if bot is None:
        return

    async with UserUnitOfWork(async_session_factory) as uow:
        tg_ids = await uow.users.list_active_tg_ids()

    await message.answer(f"Начинаю рассылку на {len(tg_ids)} пользователей...")

    sent = 0
    blocked = 0
    failed = 0
    for tg_id in tg_ids:
        try:
            await bot.send_message(chat_id=tg_id, text=text)
            sent += 1
        except TelegramRetryAfter as exc:
            await asyncio.sleep(exc.retry_after)
            try:
                await bot.send_message(chat_id=tg_id, text=text)
                sent += 1
            except Exception:
                logger.exception("Broadcast retry failed for user %s", tg_id)
                failed += 1
        except TelegramForbiddenError:
            blocked += 1
            await _deactivate_user(tg_id)
        except Exception:
            logger.exception("Broadcast failed for user %s", tg_id)
            failed += 1
        await asyncio.sleep(SEND_DELAY_SECONDS)

    await message.answer(
        f"Рассылка завершена.\nОтправлено: {sent}\nЗаблокировали бота: {blocked}\nОшибок: {failed}"
    )


async def _deactivate_user(tg_id: int) -> None:
    try:
        async with UserUnitOfWork(async_session_factory) as uow:
            user = await uow.users.get_by_tg_id(UserId(tg_id))
            if user is not None and user.is_active:
                user.is_active = False
                await uow.users.update(user)
    except Exception:
        logger.exception("Failed to deactivate user %s after broadcast-forbidden error", tg_id)
