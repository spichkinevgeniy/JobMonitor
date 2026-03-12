from io import BytesIO

import logfire
from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.application.services.user_service import UserService
from app.core.logger import get_app_logger
from app.infrastructure.db import UserUnitOfWork, async_session_factory
from app.infrastructure.llm_runtime import TemporaryLLMUnavailableError
from app.infrastructure.parsers import (
    NotAResumeError,
    ParserError,
    ParserFactory,
    TooManyPagesError,
)
from app.telegram.bot.keyboards import (
    CANCEL_BUTTON_TEXT,
    HELP_BUTTON_TEXT,
    PROFILE_BUTTON_TEXT,
    PROFILE_UPLOAD_RESUME_CALLBACK,
    UPLOAD_BUTTON_TEXT,
    get_cancel_kb,
    get_main_menu_kb,
)
from app.telegram.bot.states import BotStates
from app.telegram.bot.views import (
    build_main_menu_fallback_text,
    build_resume_cancel_text,
    build_resume_context_error_text,
    build_resume_file_too_large_text,
    build_resume_llm_unavailable_text,
    build_resume_not_a_resume_text,
    build_resume_parser_error_text,
    build_resume_processed_text,
    build_resume_processing_cancel_text,
    build_resume_processing_text,
    build_resume_prompt_text,
    build_resume_scope_text,
    build_resume_success_text,
    build_resume_too_many_pages_text,
    build_resume_unknown_error_text,
    build_resume_unsupported_format_text,
    build_resume_waiting_fallback_text,
    build_start_required_text,
)

router = Router()
logger = get_app_logger(__name__)
bot_logfire = logfire.with_tags("bot")


async def _send_resume_prompt(message: Message, state: FSMContext) -> None:
    await state.set_state(BotStates.waiting_resume)
    await message.answer(
        build_resume_prompt_text(),
        reply_markup=get_cancel_kb(),
    )


@router.callback_query(F.data == PROFILE_UPLOAD_RESUME_CALLBACK)
async def open_resume_rules_from_profile(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if not isinstance(callback.message, Message):
        return
    await _send_resume_prompt(callback.message, state)


@router.message(StateFilter(BotStates.main_menu, None), F.text == UPLOAD_BUTTON_TEXT)
async def process_upload_button(message: Message, state: FSMContext) -> None:
    await _send_resume_prompt(message, state)


@router.message(StateFilter(BotStates.waiting_resume), F.text == CANCEL_BUTTON_TEXT)
async def process_cancel(message: Message, state: FSMContext) -> None:
    await state.set_state(BotStates.main_menu)
    await message.answer(
        build_resume_cancel_text(),
        reply_markup=get_main_menu_kb(),
    )


@router.message(
    StateFilter(BotStates.waiting_resume, BotStates.main_menu, None),
    F.document,
)
async def handle_resume_document(message: Message, state: FSMContext) -> None:
    document = message.document
    if document is None:
        return

    file_name = document.file_name or ""
    file_size = document.file_size or 0
    tg_id = message.from_user.id if message.from_user is not None else None

    with bot_logfire.span(
        "bot.handle_resume_document",
        tg_id=tg_id,
        file_name=file_name,
        file_size=file_size,
    ):
        bot_logfire.info(
            "Resume upload started",
            tg_id=tg_id,
            file_name=file_name,
            file_size=file_size,
        )
        if file_size > 15 * 1024 * 1024:
            bot_logfire.info(
                "Resume rejected: file too large",
                tg_id=tg_id,
                file_name=file_name,
                file_size=file_size,
            )
            await message.answer(build_resume_file_too_large_text())
            return

        await state.set_state(BotStates.processing_resume)

        async def reset_to_menu(err_msg: str) -> None:
            await state.set_state(BotStates.main_menu)
            try:
                await message.answer(f"{err_msg}", reply_markup=get_main_menu_kb())
            except Exception:
                logger.exception("Failed to send resume error message")

        processing_message: Message | None = None
        buffer = BytesIO()
        try:
            parser = ParserFactory.get_parser_by_extension(file_name)
            processing_message = await message.answer(
                build_resume_processing_text(),
            )
            await message.answer(
                build_resume_scope_text(),
                reply_markup=get_main_menu_kb(),
            )
            user = message.from_user
            if user is None:
                bot_logfire.warning(
                    "Resume processing skipped: user context missing",
                    file_name=file_name,
                    file_size=file_size,
                )
                await reset_to_menu(build_start_required_text())
                return

            bot = message.bot
            if bot is None:
                bot_logfire.warning(
                    "Resume processing skipped: bot context missing",
                    tg_id=user.id,
                    file_name=file_name,
                    file_size=file_size,
                )
                await reset_to_menu(build_resume_context_error_text())
                return
            await bot.download(document.file_id, destination=buffer)
            dto = await parser.extract_text(buffer)

            service = UserService(UserUnitOfWork(async_session_factory))
            updated = await service.update_resume(user.id, dto)
            if not updated:
                bot_logfire.info(
                    "Resume processing skipped: user not found",
                    tg_id=user.id,
                    file_name=file_name,
                    file_size=file_size,
                )
                await reset_to_menu(build_start_required_text())
                return
            try:
                if processing_message is not None:
                    await processing_message.edit_text(build_resume_processed_text())
            except Exception:
                logger.exception("Failed to edit processing message")

            bot_logfire.info(
                "Resume processed successfully",
                tg_id=user.id,
                file_name=file_name,
                file_size=file_size,
            )
            await state.set_state(BotStates.main_menu)
            await message.answer(build_resume_success_text())

        except ValueError:
            bot_logfire.info(
                "Resume rejected: unsupported format",
                tg_id=tg_id,
                file_name=file_name,
                file_size=file_size,
            )
            await reset_to_menu(build_resume_unsupported_format_text())
        except NotAResumeError:
            bot_logfire.info(
                "Resume rejected: not a resume",
                tg_id=tg_id,
                file_name=file_name,
                file_size=file_size,
            )
            await reset_to_menu(build_resume_not_a_resume_text())
        except TooManyPagesError:
            bot_logfire.info(
                "Resume rejected: too many pages",
                tg_id=tg_id,
                file_name=file_name,
                file_size=file_size,
            )
            await reset_to_menu(build_resume_too_many_pages_text())
        except ParserError:
            bot_logfire.warning(
                "Resume rejected: parser error",
                tg_id=tg_id,
                file_name=file_name,
                file_size=file_size,
            )
            await reset_to_menu(build_resume_parser_error_text())
        except TemporaryLLMUnavailableError:
            bot_logfire.warning(
                "Resume processing delayed: llm temporarily unavailable",
                tg_id=tg_id,
                file_name=file_name,
                file_size=file_size,
            )
            await reset_to_menu(build_resume_llm_unavailable_text())
        except Exception:
            logger.exception(
                "Resume processing failed unexpectedly (tg_id=%s, file_name=%s, file_size=%s)",
                tg_id,
                file_name,
                file_size,
            )
            await reset_to_menu(build_resume_unknown_error_text())
        finally:
            buffer.close()
            if await state.get_state() == BotStates.processing_resume.state:
                await state.set_state(BotStates.main_menu)


@router.message(StateFilter(BotStates.waiting_resume))
async def waiting_resume_fallback(message: Message) -> None:
    await message.answer(
        build_resume_waiting_fallback_text(),
        reply_markup=get_cancel_kb(),
    )


@router.message(StateFilter(BotStates.processing_resume), F.text == UPLOAD_BUTTON_TEXT)
async def processing_resume_block(message: Message) -> None:
    await message.answer(build_resume_processing_text())


@router.message(StateFilter(BotStates.processing_resume), F.text == CANCEL_BUTTON_TEXT)
async def processing_resume_cancel(message: Message, state: FSMContext) -> None:
    await state.set_state(BotStates.main_menu)
    await message.answer(
        build_resume_processing_cancel_text(),
        reply_markup=get_main_menu_kb(),
    )


@router.message(StateFilter(BotStates.processing_resume), F.document)
async def processing_resume_document_block(message: Message) -> None:
    await message.answer(build_resume_processing_text())


@router.message(
    StateFilter(BotStates.main_menu, None),
    F.text,
    ~F.text.startswith("/"),
    ~F.text.in_({UPLOAD_BUTTON_TEXT, HELP_BUTTON_TEXT, PROFILE_BUTTON_TEXT}),
)
async def main_menu_fallback(message: Message) -> None:
    await message.answer(
        build_main_menu_fallback_text(),
        reply_markup=get_main_menu_kb(),
    )
