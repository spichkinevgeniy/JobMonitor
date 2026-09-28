from collections.abc import Callable
from dataclasses import dataclass
from io import BytesIO
from typing import Any

import logfire
from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Document, Message

from app.application.dto import OutResumeParse
from app.application.ports.observability_port import Feature
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
    BaseResumeParser,
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


MAX_RESUME_FILE_BYTES = 15 * 1024 * 1024


@dataclass(slots=True)
class _Upload:
    """Загрузка резюме: откуда пришла, куда отвечать и что писать в логи."""

    message: Message
    state: FSMContext
    document: Document
    tg_id: int | None
    quota: ResumeQuotaService | None

    @property
    def log_fields(self) -> dict[str, Any]:
        return {
            "user": user_ref(self.tg_id),
            "file_ext": file_ext(self.document.file_name or ""),
            "file_size": self.document.file_size or 0,
        }

    async def reset_to_menu(self, text: str) -> None:
        await self.state.set_state(BotStates.main_menu)
        try:
            await self.message.answer(text, reply_markup=get_main_menu_kb())
        except Exception:
            logger.exception("Failed to send resume error message")


# Ожидаемые отказы: запись в лог и ответ пользователю. Порядок важен:
# NotAResumeError и TooManyPagesError — наследники ParserError.
_REJECTIONS: tuple[tuple[type[Exception], Callable[..., None], str, Callable[[], str]], ...] = (
    (
        ValueError,
        bot_logfire.info,
        "Resume rejected: unsupported format",
        build_resume_unsupported_format_text,
    ),
    (
        NotAResumeError,
        bot_logfire.info,
        "Resume rejected: not a resume",
        build_resume_not_a_resume_text,
    ),
    (
        TooManyPagesError,
        bot_logfire.info,
        "Resume rejected: too many pages",
        build_resume_too_many_pages_text,
    ),
    (
        ParserError,
        bot_logfire.warning,
        "Resume rejected: parser error",
        build_resume_parser_error_text,
    ),
    (
        TemporaryLLMUnavailableError,
        bot_logfire.warning,
        "Resume processing delayed: llm temporarily unavailable",
        build_resume_llm_unavailable_text,
    ),
)


def _claim_upload(tg_id: int | None) -> bool:
    """Занимает место под загрузку; False — у пользователя уже идёт другая.

    Проверка и вставка без await между ними: FSM от гонки не спасает, её
    состояние диспетчер читает ещё до входа в хендлер.
    """
    if tg_id is None:
        return True
    if tg_id in _active_resume_uploads:
        return False
    _active_resume_uploads.add(tg_id)
    return True


def _release_upload(tg_id: int | None) -> None:
    if tg_id is not None:
        _active_resume_uploads.discard(tg_id)


@router.message(
    StateFilter(BotStates.waiting_resume, BotStates.main_menu, None),
    F.document,
)
async def handle_resume_document(message: Message, state: FSMContext) -> None:
    document = message.document
    if document is None:
        return

    tg_id = message.from_user.id if message.from_user is not None else None
    upload = _Upload(
        message=message,
        state=state,
        document=document,
        tg_id=tg_id,
        quota=ResumeQuotaService(UserUnitOfWork(async_session_factory)) if tg_id else None,
    )
    with bot_logfire.span("bot.handle_resume_document", **upload.log_fields):
        bot_logfire.info("Resume upload started", **upload.log_fields)
        if (document.file_size or 0) > MAX_RESUME_FILE_BYTES:
            bot_logfire.info("Resume rejected: file too large", **upload.log_fields)
            await message.answer(build_resume_file_too_large_text())
            return
        if not _claim_upload(tg_id):
            bot_logfire.info("Resume rejected: upload already in progress", **upload.log_fields)
            await message.answer(build_resume_processing_text())
            return

        buffer = BytesIO()
        try:
            await state.set_state(BotStates.processing_resume)
            await _process_upload(upload, buffer)
        except Exception as exc:
            await _reject(upload, exc)
        finally:
            buffer.close()
            _release_upload(tg_id)
            if await state.get_state() == BotStates.processing_resume.state:
                await state.set_state(BotStates.main_menu)


async def _process_upload(upload: _Upload, buffer: BytesIO) -> None:
    """Квота → парсер → скачивание и разбор → сохранение → ответ."""
    if not await _quota_allows(upload):
        return

    parser = ParserFactory.get_parser_by_extension(upload.document.file_name or "")
    processing = await upload.message.answer(build_resume_processing_text())
    user, bot = upload.message.from_user, upload.message.bot
    if user is None:
        bot_logfire.warning("Resume processing skipped: user context missing", **upload.log_fields)
        await upload.reset_to_menu(build_start_required_text())
        return
    if bot is None:
        bot_logfire.warning("Resume processing skipped: bot context missing", **upload.log_fields)
        await upload.reset_to_menu(build_resume_context_error_text())
        return

    dto = await _download_and_parse(upload, parser, bot, buffer)
    if dto is None:
        return

    service = UserService(UserUnitOfWork(async_session_factory))
    if not await service.update_resume(user.id, dto):
        bot_logfire.info("Resume processing skipped: user not found", **upload.log_fields)
        await upload.reset_to_menu(build_start_required_text())
        return

    await _report_success(upload, processing, dto)


async def _quota_allows(upload: _Upload) -> bool:
    """Кулдаун и дневная квота. Без tg_id считать нечего — пропускаем."""
    if upload.quota is None or upload.tg_id is None:
        return True

    decision = await upload.quota.check(upload.tg_id)
    if decision.allowed:
        return True

    bot_logfire.info("Resume rejected: quota", rejection=decision.rejection, **upload.log_fields)
    if decision.rejection is QuotaRejection.COOLDOWN:
        await upload.reset_to_menu(build_resume_cooldown_text(decision.retry_after_seconds))
    else:
        await upload.reset_to_menu(build_resume_daily_quota_text(DAILY_QUOTA))
    return False


async def _download_and_parse(
    upload: _Upload, parser: BaseResumeParser, bot: Bot, buffer: BytesIO
) -> OutResumeParse | None:
    """Скачивает и разбирает файл, заняв слот разбора.

    Слот берётся до скачивания: ожидающие не держат буферы. В квоту
    загрузка засчитывается, только когда слот получен.
    """
    async with acquire_parse_slot() as granted:
        if not granted:
            bot_logfire.warning("Resume rejected: no free parse slot", **upload.log_fields)
            await upload.reset_to_menu(build_resume_busy_text())
            return None
        if upload.quota is not None and upload.tg_id is not None:
            await upload.quota.register(upload.tg_id)
        observe_feature(Feature.RESUME_UPLOAD)
        await bot.download(upload.document.file_id, destination=buffer)
        return await parser.extract_text(buffer)


async def _report_success(upload: _Upload, processing: Message, dto: OutResumeParse) -> None:
    try:
        await processing.edit_text(build_resume_processed_text())
    except Exception:
        logger.exception("Failed to edit processing message")

    bot_logfire.info("Resume processed successfully", **upload.log_fields)
    await upload.state.set_state(BotStates.main_menu)
    await upload.message.answer(
        build_resume_result_text(
            sorted({item.specialization.value for item in dto.specializations}),
            sorted({item.skill.value for item in dto.skills}),
        ),
        reply_markup=get_resume_result_kb(build_specialty_url()),
    )


async def _reject(upload: _Upload, exc: Exception) -> None:
    for error_type, write_log, event, build_text in _REJECTIONS:
        if isinstance(exc, error_type):
            write_log(event, **upload.log_fields)
            await upload.reset_to_menu(build_text())
            return

    logger.error(
        "Resume processing failed unexpectedly (user=%s, ext=%s, size=%s)",
        user_ref(upload.tg_id),
        file_ext(upload.document.file_name or ""),
        upload.document.file_size or 0,
        exc_info=exc,
    )
    await upload.reset_to_menu(build_resume_unknown_error_text())


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
