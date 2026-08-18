from io import BytesIO

import logfire
from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.application.ports.observability_port import Feature
from app.application.services.resume_import_service import MAX_RESUME_BYTES
from app.application.services.resume_quota_service import (
    DAILY_QUOTA,
    QuotaRejection,
    ResumeQuotaService,
)
from app.application.services.user_service import UserService
from app.core.logger import get_app_logger
from app.core.privacy import file_ext, user_ref
from app.infrastructure.db import UserUnitOfWork, async_session_factory
from app.infrastructure.llm_runtime import TemporaryLLMUnavailableError
from app.infrastructure.observability import observe_feature
from app.infrastructure.parsers import (
    NotAResumeError,
    ParserError,
    ParserFactory,
    TooManyPagesError,
)
from app.infrastructure.parsers.concurrency import acquire_parse_slot
from app.telegram.bot.keyboards import (
    CANCEL_BUTTON_TEXT,
    MAIN_MENU_BUTTON_TEXTS,
    PROFILE_UPLOAD_RESUME_CALLBACK,
    RESUME_CONFIRM_CALLBACK,
    UPLOAD_BUTTON_TEXT,
    get_cancel_kb,
    get_main_menu_kb,
    get_resume_result_kb,
)
from app.telegram.bot.states import BotStates
from app.telegram.bot.views import (
    build_main_menu_fallback_text,
    build_resume_busy_text,
    build_resume_cancel_text,
    build_resume_confirmed_text,
    build_resume_context_error_text,
    build_resume_cooldown_text,
    build_resume_daily_quota_text,
    build_resume_file_too_large_text,
    build_resume_llm_unavailable_text,
    build_resume_not_a_resume_text,
    build_resume_parser_error_text,
    build_resume_processed_text,
    build_resume_processing_cancel_text,
    build_resume_processing_text,
    build_resume_prompt_text,
    build_resume_result_text,
    build_resume_too_many_pages_text,
    build_resume_unknown_error_text,
    build_resume_unsupported_format_text,
    build_resume_waiting_fallback_text,
    build_specialty_url,
    build_start_required_text,
)

router = Router()
logger = get_app_logger(__name__)
bot_logfire = logfire.with_tags("bot")

_active_resume_uploads: set[int] = set()


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
        user=user_ref(tg_id),
        file_ext=file_ext(file_name),
        file_size=file_size,
    ):
        bot_logfire.info(
            "Resume upload started",
            user=user_ref(tg_id),
            file_ext=file_ext(file_name),
            file_size=file_size,
        )
        if file_size > MAX_RESUME_BYTES:
            bot_logfire.info(
                "Resume rejected: file too large",
                user=user_ref(tg_id),
                file_ext=file_ext(file_name),
                file_size=file_size,
            )
            await message.answer(build_resume_file_too_large_text())
            return

        # Проверка и вставка без await между ними: FSM от гонки не спасает,
        # её состояние диспетчер читает ещё до входа в хендлер.
        if tg_id is not None:
            if tg_id in _active_resume_uploads:
                bot_logfire.info(
                    "Resume rejected: upload already in progress",
                    user=user_ref(tg_id),
                    file_ext=file_ext(file_name),
                    file_size=file_size,
                )
                await message.answer(build_resume_processing_text())
                return
            _active_resume_uploads.add(tg_id)

        async def reset_to_menu(err_msg: str) -> None:
            await state.set_state(BotStates.main_menu)
            try:
                await message.answer(f"{err_msg}", reply_markup=get_main_menu_kb())
            except Exception:
                logger.exception("Failed to send resume error message")

        processing_message: Message | None = None
        buffer = BytesIO()
        try:
            await state.set_state(BotStates.processing_resume)

            quota: ResumeQuotaService | None = None
            if tg_id is not None:
                quota = ResumeQuotaService(UserUnitOfWork(async_session_factory))
                decision = await quota.check(tg_id)
                if not decision.allowed:
                    bot_logfire.info(
                        "Resume rejected: quota",
                        user=user_ref(tg_id),
                        rejection=decision.rejection,
                        file_ext=file_ext(file_name),
                    )
                    if decision.rejection is QuotaRejection.COOLDOWN:
                        await reset_to_menu(
                            build_resume_cooldown_text(decision.retry_after_seconds)
                        )
                    else:
                        await reset_to_menu(build_resume_daily_quota_text(DAILY_QUOTA))
                    return

            parser = ParserFactory.get_parser_by_extension(file_name)
            processing_message = await message.answer(
                build_resume_processing_text(),
            )
            user = message.from_user
            if user is None:
                bot_logfire.warning(
                    "Resume processing skipped: user context missing",
                    file_ext=file_ext(file_name),
                    file_size=file_size,
                )
                await reset_to_menu(build_start_required_text())
                return

            bot = message.bot
            if bot is None:
                bot_logfire.warning(
                    "Resume processing skipped: bot context missing",
                    user=user_ref(user.id),
                    file_ext=file_ext(file_name),
                    file_size=file_size,
                )
                await reset_to_menu(build_resume_context_error_text())
                return
            # Слот до скачивания: ожидающие не держат буферы.
            async with acquire_parse_slot() as granted:
                if not granted:
                    bot_logfire.warning(
                        "Resume rejected: no free parse slot",
                        user=user_ref(tg_id),
                        file_ext=file_ext(file_name),
                    )
                    await reset_to_menu(build_resume_busy_text())
                    return
                if quota is not None and tg_id is not None:
                    await quota.register(tg_id)
                observe_feature(Feature.RESUME_UPLOAD)
                await bot.download(document.file_id, destination=buffer)
                dto = await parser.extract_text(buffer)

            service = UserService(UserUnitOfWork(async_session_factory))
            updated = await service.update_resume(user.id, dto)
            if not updated:
                bot_logfire.info(
                    "Resume processing skipped: user not found",
                    user=user_ref(user.id),
                    file_ext=file_ext(file_name),
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
                user=user_ref(user.id),
                file_ext=file_ext(file_name),
                file_size=file_size,
            )
            await state.set_state(BotStates.main_menu)
            await message.answer(
                build_resume_result_text(
                    sorted({item.specialization.value for item in dto.specializations}),
                    sorted({item.skill.value for item in dto.skills}),
                ),
                reply_markup=get_resume_result_kb(build_specialty_url()),
            )

        except ValueError:
            bot_logfire.info(
                "Resume rejected: unsupported format",
                user=user_ref(tg_id),
                file_ext=file_ext(file_name),
                file_size=file_size,
            )
            await reset_to_menu(build_resume_unsupported_format_text())
        except NotAResumeError:
            bot_logfire.info(
                "Resume rejected: not a resume",
                user=user_ref(tg_id),
                file_ext=file_ext(file_name),
                file_size=file_size,
            )
            await reset_to_menu(build_resume_not_a_resume_text())
        except TooManyPagesError:
            bot_logfire.info(
                "Resume rejected: too many pages",
                user=user_ref(tg_id),
                file_ext=file_ext(file_name),
                file_size=file_size,
            )
            await reset_to_menu(build_resume_too_many_pages_text())
        except ParserError:
            bot_logfire.warning(
                "Resume rejected: parser error",
                user=user_ref(tg_id),
                file_ext=file_ext(file_name),
                file_size=file_size,
            )
            await reset_to_menu(build_resume_parser_error_text())
        except TemporaryLLMUnavailableError:
            bot_logfire.warning(
                "Resume processing delayed: llm temporarily unavailable",
                user=user_ref(tg_id),
                file_ext=file_ext(file_name),
                file_size=file_size,
            )
            await reset_to_menu(build_resume_llm_unavailable_text())
        except Exception:
            logger.exception(
                "Resume processing failed unexpectedly (user=%s, ext=%s, size=%s)",
                user_ref(tg_id),
                file_ext(file_name),
                file_size,
            )
            await reset_to_menu(build_resume_unknown_error_text())
        finally:
            buffer.close()
            if tg_id is not None:
                _active_resume_uploads.discard(tg_id)
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
    ~F.text.in_(MAIN_MENU_BUTTON_TEXTS | {UPLOAD_BUTTON_TEXT}),
)
async def main_menu_fallback(message: Message) -> None:
    await message.answer(
        build_main_menu_fallback_text(),
        reply_markup=get_main_menu_kb(),
    )


@router.callback_query(F.data == RESUME_CONFIRM_CALLBACK)
async def confirm_resume_result(callback: CallbackQuery) -> None:
    await callback.answer()
    if not isinstance(callback.message, Message):
        return
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        logger.debug("Failed to drop resume confirmation keyboard", exc_info=True)
    await callback.message.answer(build_resume_confirmed_text(), reply_markup=get_main_menu_kb())
