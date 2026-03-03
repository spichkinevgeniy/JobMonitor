from io import BytesIO

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.application.services.user_service import UserService
from app.core.logger import get_app_logger
from app.infrastructure.db import UserUnitOfWork, async_session_factory
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
    TRACKING_BUTTON_TEXT,
    UPLOAD_BUTTON_TEXT,
    get_cancel_kb,
    get_main_menu_kb,
)
from app.telegram.bot.states import BotStates

router = Router()
logger = get_app_logger(__name__)


@router.message(StateFilter(BotStates.main_menu, None), F.text == UPLOAD_BUTTON_TEXT)
async def process_upload_button(message: Message, state: FSMContext) -> None:
    await state.set_state(BotStates.waiting_resume)
    await message.answer(
        "Пришли, пожалуйста, своё резюме файлом в формате PDF. 📄\n"
        "Я сразу приступлю к его изучению.",
        reply_markup=get_cancel_kb(),
    )


@router.message(StateFilter(BotStates.waiting_resume), F.text == CANCEL_BUTTON_TEXT)
async def process_cancel(message: Message, state: FSMContext) -> None:
    await state.set_state(BotStates.main_menu)
    await message.answer(
        "Понял, отменяем. Твои текущие настройки остались без изменений. ↩️",
        reply_markup=get_main_menu_kb(),
    )


@router.message(StateFilter(BotStates.waiting_resume), F.document)
async def handle_resume_document(message: Message, state: FSMContext) -> None:
    document = message.document
    if document is None:
        return
    if document.file_size and document.file_size > 15 * 1024 * 1024:
        await message.answer("Файл слишком большой. Максимум 15 МБ.")
        return

    file_name = document.file_name or ""

    await state.set_state(BotStates.processing_resume)

    async def reset_to_menu(err_msg: str) -> None:
        await message.answer(f"⚠️ {err_msg}", reply_markup=get_main_menu_kb())
        await state.set_state(BotStates.main_menu)

    try:
        parser = ParserFactory.get_parser_by_extension(file_name)
    except ValueError:
        await reset_to_menu("Формат не поддерживается.")
        return

    processing_message = await message.answer(
        "⏳ Резюме в обработке. Обычно это занимает 1–2 минуты.",
    )
    await message.answer(
        "Что я учитываю при подборе: 🎯\n"
        "• Специализацию (Backend, Frontend, Fullstack и др.)\n"
        "• Основные языки (Python, Java, C# и др.)\n"
        "• Доп. фильтры из настроек: опыт, зарплата, формат\n\n"
        "Если в резюме указано несколько направлений или языков, я учту все.",
        reply_markup=get_main_menu_kb(),
    )
    user = message.from_user
    if user is None:
        await reset_to_menu("Нажмите «Начать пользоваться ботом», чтобы продолжить.")
        return

    buffer = BytesIO()
    try:
        await message.bot.download(document.file_id, destination=buffer)
        dto = await parser.extract_text(buffer)

        service = UserService(UserUnitOfWork(async_session_factory))
        updated = await service.update_resume(user.id, dto)
        if not updated:
            await reset_to_menu("Нажмите «Начать пользоваться ботом», чтобы продолжить.")
            return
        try:
            await processing_message.edit_text("✅ Резюме обработалось.")
        except Exception as e:
            logger.error(f"Failed to edit message: {e}")

        await message.answer(
            "Отслеживание включено: теперь я буду присылать подходящие вакансии. 🔎"
        )
        await state.set_state(BotStates.main_menu)

    except NotAResumeError:
        await reset_to_menu("Этот файл не похож на резюме.")
    except TooManyPagesError:
        await reset_to_menu("Слишком много страниц (макс. 10).")
    except ParserError:
        await reset_to_menu("Не удалось обработать файл.")
    except Exception:
        logger.exception("Resume parsing failed")
        await reset_to_menu("Произошла ошибка при анализе.")
    finally:
        buffer.close()


@router.message(StateFilter(BotStates.waiting_resume))
async def waiting_resume_fallback(message: Message) -> None:
    await message.answer(
        "Чтобы продолжить, мне нужен твой PDF-файл. 📄\n"
        "Текст или фото я прочитать не смогу.\n\n"
        "Жду резюме или нажми «Отмена», чтобы вернуться в меню.",
        reply_markup=get_cancel_kb(),
    )


@router.message(StateFilter(BotStates.processing_resume), F.text == UPLOAD_BUTTON_TEXT)
async def processing_resume_block(message: Message) -> None:
    await message.answer("Резюме уже в обработке. Обычно это занимает 1–2 минуты.")


@router.message(StateFilter(BotStates.processing_resume), F.document)
async def processing_resume_document_block(message: Message) -> None:
    await message.answer("Резюме уже в обработке. Обычно это занимает 1–2 минуты.")


@router.message(
    StateFilter(BotStates.main_menu, None),
    ~F.text.in_(
        {UPLOAD_BUTTON_TEXT, TRACKING_BUTTON_TEXT, HELP_BUTTON_TEXT, PROFILE_BUTTON_TEXT}
    ),
)
async def main_menu_fallback(message: Message) -> None:
    await message.answer(
        "Используйте кнопки меню.",
        reply_markup=get_main_menu_kb(),
    )
