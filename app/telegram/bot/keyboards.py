from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

START_BUTTON_TEXT = "Открыть бота"
UPLOAD_BUTTON_TEXT = "📄 Обновить резюме"
CANCEL_BUTTON_TEXT = "❌ Отмена"
HELP_BUTTON_TEXT = "❓ Как это работает?"
PROFILE_BUTTON_TEXT = "👤 Мой профиль"

PROFILE_FILL_FORM_BUTTON_TEXT = "⚙️ Настроить профиль"
PROFILE_UPLOAD_RESUME_BUTTON_TEXT = "📄 Загрузить резюме"
PROFILE_FILL_FORM_CALLBACK = "profile:fill_form"
PROFILE_UPLOAD_RESUME_CALLBACK = "profile:upload_resume"
SETTINGS_DONE_BUTTON_TEXT = "✅ Готов"
SETTINGS_DONE_CALLBACK = "settings:done"


def get_main_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=PROFILE_BUTTON_TEXT)
    builder.button(text=HELP_BUTTON_TEXT)
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def get_start_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=START_BUTTON_TEXT)
    return builder.as_markup(resize_keyboard=True)


def get_cancel_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=CANCEL_BUTTON_TEXT)
    return builder.as_markup(resize_keyboard=True)


def get_profile_actions_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=PROFILE_FILL_FORM_BUTTON_TEXT,
        callback_data=PROFILE_FILL_FORM_CALLBACK,
    )
    builder.button(
        text=PROFILE_UPLOAD_RESUME_BUTTON_TEXT,
        callback_data=PROFILE_UPLOAD_RESUME_CALLBACK,
    )
    builder.adjust(1, 1)
    return builder.as_markup()


def get_settings_menu_kb(
    specialty_and_skills_label: str,
    format_label: str,
    salary_label: str,
    level_label: str,
    specialty_url: str,
    format_url: str,
    salary_url: str,
    level_url: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"🧩 {specialty_and_skills_label}",
        web_app=WebAppInfo(url=specialty_url),
    )
    builder.button(
        text=f"🏢 {format_label}",
        web_app=WebAppInfo(url=format_url),
    )
    builder.button(
        text=f"💰 {salary_label}",
        web_app=WebAppInfo(url=salary_url),
    )
    builder.button(
        text=f"📈 {level_label}",
        web_app=WebAppInfo(url=level_url),
    )
    builder.button(
        text=SETTINGS_DONE_BUTTON_TEXT,
        callback_data=SETTINGS_DONE_CALLBACK,
    )
    builder.adjust(1, 1, 1, 1, 1)
    return builder.as_markup()
