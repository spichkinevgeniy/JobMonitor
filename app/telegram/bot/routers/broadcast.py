import asyncio

from aiogram import Router
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from app.application.services.user_service import UserService
from app.core.config import config
from app.core.logger import get_app_logger
from app.core.privacy import user_ref
from app.telegram.bot.delivery import deactivate_user
from app.telegram.bot.keyboards import get_main_menu_kb

router = Router()
logger = get_app_logger(__name__)

SEND_DELAY_SECONDS = 0.05


@router.message(Command("broadcast"))
async def cmd_broadcast(
    message: Message, command: CommandObject, user_service: UserService
) -> None:
    if message.from_user is None or message.from_user.id not in config.ADMIN_IDS:
        return

    text = command.args
    if not text:
        await message.answer("Использование: /broadcast <текст сообщения>")
        return

    bot = message.bot
    if bot is None:
        return

    tg_ids = await user_service.list_active_tg_ids()

    await message.answer(f"Начинаю рассылку на {len(tg_ids)} пользователей...")

    sent = 0
    blocked = 0
    failed = 0
    for tg_id in tg_ids:
        try:
            await bot.send_message(chat_id=tg_id, text=text, reply_markup=get_main_menu_kb())
            sent += 1
        except TelegramRetryAfter as exc:
            await asyncio.sleep(exc.retry_after)
            try:
                await bot.send_message(chat_id=tg_id, text=text, reply_markup=get_main_menu_kb())
                sent += 1
            except Exception:
                logger.exception("Broadcast retry failed for user %s", user_ref(tg_id))
                failed += 1
        except TelegramForbiddenError:
            blocked += 1
            await deactivate_user(user_service, tg_id)
        except Exception:
            logger.exception("Broadcast failed for user %s", user_ref(tg_id))
            failed += 1
        await asyncio.sleep(SEND_DELAY_SECONDS)

    await message.answer(
        f"Рассылка завершена.\nОтправлено: {sent}\nЗаблокировали бота: {blocked}\nОшибок: {failed}"
    )
