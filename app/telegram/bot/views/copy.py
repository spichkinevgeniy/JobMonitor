SUPPORT_BOT_HANDLE = "@JobMonitor_Support_Bot"


def build_available_commands_text() -> str:
    return (
        "/profile — открыть профиль поиска\n\n"
        "/settings — настроить профиль и фильтры\n\n"
        "/help — посмотреть, как это работает"
    )


def build_start_message(*, is_new: bool) -> str:
    if not is_new:
        return (
            "Вы уже зарегистрированы в боте. Вот список доступных команд 👇\n\n"
            f"{build_available_commands_text()}"
        )

    return (
        "Этот бот появился из простой причины: вручную мониторить вакансии в Telegram "
        "быстро надоедает.\n\n"
        "Бот отслеживает Telegram-каналы, отсекает лишний шум и присылает вакансии, "
        "которые ближе к вашему профилю.\n\n"
        "Дальше можно перейти в один из разделов:\n"
        f"{build_available_commands_text()}"
    )


def build_start_required_text() -> str:
    return "Чтобы открыть меню, нажмите «Открыть бота»."


def build_help_text() -> str:
    return (
        "❓ Как это работает\n\n"
        "Надоело мониторить вакансии по каналам, а в ответ получать рекламу, дубли и случайный шум? "
        "Этот бот как раз для этого и собирался.\n\n\n"
        "🔎 Он отслеживает Telegram-каналы с вакансиями, выделяет релевантные предложения и присылает "
        "только то, что ближе к вашему профилю.\n\n\n"
        "⚙️ Профиль можно настроить двумя способами:\n"
        "1. Открыть /settings и задать параметры вручную.\n"
        "2. Загрузить PDF-резюме, чтобы бот собрал профиль из него.\n\n\n"
        "🛠️ Проект поддерживает независимый разработчик. Если подходящая вакансия не пришла, "
        "возможно, фильтры были настроены слишком строго или нужного Telegram-канала пока нет в подборке.\n"
        f"\n💬 Связаться, предложить канал для мониторинга или оставить обратную связь можно через {SUPPORT_BOT_HANDLE}."
    )


def build_settings_intro_text() -> str:
    return (
        "⚙️ Настройки вашего профиля\n\n"
        "Каждый раздел открывается на отдельной странице настройки.\n"
        "Изменения сохраняются только для того раздела, который был открыт."
    )


def build_settings_unavailable_text() -> str:
    return (
        "Страницы настройки сейчас недоступны.\n"
        f"Если проблема повторяется, можно написать в {SUPPORT_BOT_HANDLE}."
    )


def build_settings_saved_text() -> str:
    return "Параметры профиля обновлены."


def build_resume_prompt_text() -> str:
    return (
        "📄 Загрузка резюме\n\n"
        "Для этого шага нужен PDF-файл.\n"
        "Ограничения: до 15 МБ и до 10 страниц.\n\n"
        "Отправьте резюме файлом, и бот обновит профиль поиска по его содержимому."
    )


def build_resume_scope_text() -> str:
    return (
        "🧠 Бот учитывает вашу специализацию и основные навыки.\n\n"
        "Если бот найдет лишнее, настройте ваш профиль через форму."
    )


def build_resume_waiting_fallback_text() -> str:
    return (
        "Для продолжения нужен PDF-файл с резюме.\n"
        "Текстовые сообщения и изображения на этом шаге не подойдут.\n\n"
        "Можно отправить резюме сейчас или нажать «Отмена»."
    )


def build_resume_cancel_text() -> str:
    return "Загрузка отменена. Текущий профиль остался без изменений."


def build_resume_processing_text() -> str:
    return "Резюме обрабатывается. Обычно это занимает 1-2 минуты."


def build_resume_processed_text() -> str:
    return "Резюме обработано."


def build_resume_success_text() -> str:
    return "Профиль обновлен по резюме. Теперь бот будет присылать более точные совпадения."


def build_resume_processing_cancel_text() -> str:
    return "Обработка остановлена. Резюме можно отправить заново в любой момент."


def build_main_menu_fallback_text() -> str:
    return "Используйте кнопки меню или команды /profile, /settings и /help."


def build_resume_file_too_large_text() -> str:
    return "Файл больше 15 МБ. Нужен более компактный PDF."


def build_resume_context_error_text() -> str:
    return "Не удалось получить контекст бота. Попробуйте еще раз."


def build_resume_unsupported_format_text() -> str:
    return "Для этого шага подходит только PDF."


def build_resume_not_a_resume_text() -> str:
    return "Файл не похож на резюме."


def build_resume_too_many_pages_text() -> str:
    return "В резюме больше 10 страниц. Нужен более компактный PDF."


def build_resume_parser_error_text() -> str:
    return "Не удалось разобрать файл."


def build_resume_unknown_error_text() -> str:
    return "Во время разбора резюме произошла ошибка."
