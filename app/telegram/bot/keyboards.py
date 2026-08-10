from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

START_BUTTON_TEXT = "Открыть бота"
UPLOAD_BUTTON_TEXT = "📄 Обновить резюме"
CANCEL_BUTTON_TEXT = "❌ Отмена"
HELP_BUTTON_TEXT = "❓ Как это работает?"
PROFILE_BUTTON_TEXT = "👤 Мой профиль"

PROFILE_FILL_FORM_BUTTON_TEXT = "⚙️ Настроить профиль"
PROFILE_UPLOAD_RESUME_BUTTON_TEXT = "📄 Загрузить резюме"
PROFILE_STATS_BUTTON_TEXT = "📊 Аналитика"
PROFILE_FILL_FORM_CALLBACK = "profile:fill_form"
PROFILE_UPLOAD_RESUME_CALLBACK = "profile:upload_resume"
VACANCY_WHY_BUTTON_TEXT = "Почему прислали?"
VACANCY_REJECT_BUTTON_TEXT = "Не подходит"
VACANCY_REJECTED_BUTTON_TEXT = "✓ Отмечена как неподходящая · отменить"
VACANCY_UNDO_CALLBACK_PREFIX = "vac:undo:"
VACANCY_WHY_CALLBACK_PREFIX = "vac:why:"
VACANCY_REJECT_CALLBACK_PREFIX = "vac:no:"

RESUME_CONFIRM_BUTTON_TEXT = "Всё верно"
RESUME_FIX_BUTTON_TEXT = "Поправить"
RESUME_CONFIRM_CALLBACK = "resume:confirm"

SETTINGS_DONE_BUTTON_TEXT = "✅ Готов"
SETTINGS_DONE_CALLBACK = "settings:done"


# Кнопки главного меню шлют обычный текст, поэтому fallback обязан их
# пропускать — иначе новая кнопка молча уходит в «используйте кнопки меню».
MAIN_MENU_BUTTON_TEXTS = frozenset(
    {PROFILE_BUTTON_TEXT, PROFILE_STATS_BUTTON_TEXT, HELP_BUTTON_TEXT}
)


def get_main_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=PROFILE_BUTTON_TEXT)
    builder.button(text=PROFILE_STATS_BUTTON_TEXT)
    builder.button(text=HELP_BUTTON_TEXT)
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)


def get_start_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=START_BUTTON_TEXT)
    return builder.as_markup(resize_keyboard=True)


def get_cancel_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=CANCEL_BUTTON_TEXT)
    return builder.as_markup(resize_keyboard=True)


def get_stats_kb(stats_url: str) -> InlineKeyboardMarkup:
    """Мини-апп открываем только отсюда: кнопке reply-клавиатуры Telegram не
    передаёт подписанные данные, и авторизоваться там нечем."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=PROFILE_STATS_BUTTON_TEXT,
        web_app=WebAppInfo(url=stats_url),
    )
    return builder.as_markup()


def get_profile_actions_kb(stats_url: str = "") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=PROFILE_FILL_FORM_BUTTON_TEXT,
        callback_data=PROFILE_FILL_FORM_CALLBACK,
    )
    builder.button(
        text=PROFILE_UPLOAD_RESUME_BUTTON_TEXT,
        callback_data=PROFILE_UPLOAD_RESUME_CALLBACK,
    )
    if stats_url:
        builder.button(
            text=PROFILE_STATS_BUTTON_TEXT,
            web_app=WebAppInfo(url=stats_url),
        )
    builder.adjust(1)
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


def get_vacancy_kb(
    vacancy_id: str,
    *,
    rejected: bool = False,
    source_channel: str | None = None,
    source_url: str | None = None,
) -> InlineKeyboardMarkup:
    """Кнопки под вакансией. В callback_data влезает 64 байта, UUID с
    префиксом занимает 44.

    После отметки «не подходит» объяснение остаётся доступным: человек может
    захотеть понять, почему ему это вообще прислали.

    Кнопка источника заменяет шапку «Переслано из», которая была у пересылки:
    ведёт не в канал, а сразу на исходный пост, и имя канала видно без нажатия.
    """
    builder = InlineKeyboardBuilder()
    rows: list[int] = []

    builder.button(
        text=VACANCY_WHY_BUTTON_TEXT,
        callback_data=f"{VACANCY_WHY_CALLBACK_PREFIX}{vacancy_id}",
    )
    if rejected:
        builder.button(
            text=VACANCY_REJECTED_BUTTON_TEXT,
            callback_data=f"{VACANCY_UNDO_CALLBACK_PREFIX}{vacancy_id}",
        )
        rows += [1, 1]
    else:
        builder.button(
            text=VACANCY_REJECT_BUTTON_TEXT,
            callback_data=f"{VACANCY_REJECT_CALLBACK_PREFIX}{vacancy_id}",
        )
        rows += [2]

    if source_url:
        label = f"Источник: {source_channel}" if source_channel else "Источник"
        builder.button(text=f"↗ {label}", url=source_url)
        rows += [1]

    builder.adjust(*rows)
    return builder.as_markup()


def get_resume_result_kb(specialty_url: str = "") -> InlineKeyboardMarkup:
    """Подтверждение разбора резюме. «Поправить» ведёт сразу в настройку
    профиля, чтобы человеку не пришлось искать её самому."""
    builder = InlineKeyboardBuilder()
    builder.button(text=RESUME_CONFIRM_BUTTON_TEXT, callback_data=RESUME_CONFIRM_CALLBACK)
    if specialty_url:
        builder.button(text=RESUME_FIX_BUTTON_TEXT, web_app=WebAppInfo(url=specialty_url))
        builder.adjust(2)
    else:
        builder.adjust(1)
    return builder.as_markup()
