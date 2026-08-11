from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, Message, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.application.services.developer_user_service import DeveloperUserService
from app.core.config import config
from app.infrastructure.db import DeveloperUserUnitOfWork, async_session_factory

router = Router(name="developer")


def is_developer_user_allowed(tg_id: int) -> bool:
    return config.APP_ENV == "development" and tg_id in config.DEV_TELEGRAM_IDS


def _build_service() -> DeveloperUserService:
    return DeveloperUserService(DeveloperUserUnitOfWork(async_session_factory))


def build_developer_miniapp_keyboard(
    *, onboarding_completed: bool = False
) -> InlineKeyboardMarkup | None:
    base_url = config.MINI_APP_BASE_URL.strip().rstrip("/")
    if not base_url:
        return None

    builder = InlineKeyboardBuilder()
    path = "/miniapp/dashboard/" if onboarding_completed else "/miniapp/react/?mode=onboarding"
    builder.button(
        text="Open Dashboard" if onboarding_completed else "Open React onboarding",
        web_app=WebAppInfo(url=f"{base_url}{path}"),
    )
    return builder.as_markup()


@router.message(Command("dev_reset_me"))
async def cmd_dev_reset_me(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not is_developer_user_allowed(message.from_user.id):
        return

    if await _build_service().reset_profile(message.from_user.id):
        await state.clear()
        await message.answer(
            "Dev profile reset. Open onboarding again.",
            reply_markup=build_developer_miniapp_keyboard(),
        )


@router.message(Command("dev_delete_me"))
async def cmd_dev_delete_me(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not is_developer_user_allowed(message.from_user.id):
        return

    if await _build_service().delete_user(message.from_user.id):
        await state.clear()
        await message.answer("Dev user deleted. Send /start to register again.")


__all__ = [
    "build_developer_miniapp_keyboard",
    "is_developer_user_allowed",
    "router",
]
