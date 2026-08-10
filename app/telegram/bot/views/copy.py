SUPPORT_BOT_HANDLE = "@JobMonitor_Support_Bot"


def build_available_commands_text() -> str:
    return (
        "/profile - открыть профиль поиска\n\n"
        "/settings - настроить профиль и фильтры\n\n"
        "/help - посмотреть, как это работает"
    )


def build_start_message(*, is_new: bool) -> str:
    if not is_new:
        return (
            "Вы уже зарегистрированы в боте. Вот список доступных команд.\n\n"
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
    return 'Чтобы открыть меню, нажмите "Открыть бота".'


def build_help_text() -> str:
    return (
        "❓Как это работает\n\n"
        "🔎 Надоело мониторить вакансии по каналам, а в ответ получать рекламу, дубли "
        "и случайный шум? Этот бот как раз для этого и собирался.\n\n"
        "🤖 Он отслеживает Telegram-каналы с вакансиями, выделяет релевантные предложения "
        "и присылает только то, что ближе к вашему профилю.\n\n"
        "⚙️ Профиль можно настроить двумя способами:\n"
        "1. Открыть /settings и задать параметры вручную.\n"
        "2. Загрузить PDF-резюме, чтобы бот собрал профиль из него.\n\n"
        "🛠 Проект поддерживает независимый разработчик. Если подходящая вакансия не пришла, "
        "возможно, фильтры были настроены слишком строго или нужного Telegram-канала "
        "пока нет в подборке.\n\n"
        f"💬 Связаться, предложить канал для мониторинга или оставить обратную связь "
        f"можно через {SUPPORT_BOT_HANDLE}."
    )


def build_settings_intro_text() -> str:
    return (
        "Настройки вашего профиля\n\n"
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
        "Загрузка резюме\n\n"
        "Для этого шага нужен PDF-файл.\n"
        "Ограничения: до 15 МБ и до 10 страниц.\n\n"
        "Отправьте резюме файлом, и бот обновит профиль поиска по его содержимому."
    )


def build_resume_waiting_fallback_text() -> str:
    return (
        "Для продолжения нужен PDF-файл с резюме.\n"
        "Текстовые сообщения и изображения на этом шаге не подойдут.\n\n"
        'Можно отправить резюме сейчас или нажать "Отмена".'
    )


def build_resume_cancel_text() -> str:
    return "Загрузка отменена. Текущий профиль остался без изменений."


def build_resume_processing_text() -> str:
    return "Резюме обрабатывается. Обычно это занимает 1-2 минуты."


def build_resume_processed_text() -> str:
    return "Резюме обработано."


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


def build_resume_cooldown_text(seconds: int) -> str:
    return f"Слишком часто. Следующее резюме можно прислать через {seconds} с."


def build_resume_daily_quota_text(quota: int) -> str:
    return (
        f"На сегодня лимит исчерпан: {quota} резюме в сутки. "
        "Попробуйте завтра — профиль при этом сохранён."
    )


def build_resume_busy_text() -> str:
    return "Сейчас разбираем другие резюме. Попробуйте через пару минут."


def build_resume_parser_error_text() -> str:
    return "Не удалось разобрать файл."


def build_resume_unknown_error_text() -> str:
    return "Во время разбора резюме произошла ошибка."


def build_resume_llm_unavailable_text() -> str:
    return "Сейчас модель временно перегружена. Попробуйте еще раз чуть позже."


def build_stats_prompt_text() -> str:
    return "Аналитика по вашему профилю: сколько вакансий подходит, что отсекают фильтры и кто нанимает."


def build_stats_unavailable_text() -> str:
    return (
        "Страница аналитики сейчас недоступна.\n"
        f"Если проблема повторяется, можно написать в {SUPPORT_BOT_HANDLE}."
    )


def build_resume_result_text(specializations: list[str], skills: list[str]) -> str:
    """Показываем, что поняли, и просим подтвердить.

    Раньше бот заранее предупреждал «если найдёт лишнее — настройте профиль»
    и на этом всё. Что именно извлеклось, человек не видел никогда: отсюда
    профили с одним навыком и с чужими специализациями, о которых владельцы
    не подозревали.
    """
    lines = ["Разобрал резюме. Понял так:", ""]
    lines.append(
        f"Специализация: {', '.join(specializations)}"
        if specializations
        else "Специализация: не нашёл"
    )
    lines.append(f"Навыки: {', '.join(skills)}" if skills else "Навыки: не нашёл")
    lines.append("")
    lines.append("По ним бот и подбирает вакансии. Всё верно?")
    return "\n".join(lines)


def build_resume_confirmed_text() -> str:
    return "Отлично, профиль сохранён. Вакансии начнут приходить по нему."


_USER_FORMAT_TITLES = {
    "REMOTE": "только удалёнка",
    "ONSITE": "только офис",
    "HYBRID": "только гибрид",
}


def build_vacancy_reason_text(
    matched_specializations: list[str],
    matched_skills: list[str],
    caveats: list[str],
) -> str:
    """Отвечает на «почему мне», а не пересказывает вакансию.

    Грейд, формат и зарплату человек читает в самом объявлении — оно прямо
    над кнопкой. Единственное, чего он знать не может, — какая часть его
    профиля сработала. Остальное объясняем, только когда вакансия прошла
    вопреки его же настройке: иначе это отчёт алгоритма, а не помощь.
    """
    matched = " · ".join(matched_specializations + matched_skills)
    lines = [f"Совпало с вашим профилем: {matched}" if matched else "Совпадений с профилем нет"]
    lines.extend(caveats)
    return "\n".join(lines)


def build_reason_caveat_format(user_format: str) -> str:
    title = _USER_FORMAT_TITLES.get(user_format, user_format)
    return f"Формат работы в объявлении не указан — поэтому прошла, хотя у вас «{title}»"


def build_reason_caveat_grade() -> str:
    return "Грейд в объявлении не указан — поэтому прошла, хотя у вас есть фильтр по уровню"


def build_reason_caveat_experience() -> str:
    return "Опыт в объявлении не указан — поэтому прошла, хотя у вас есть фильтр по опыту"


def build_reason_caveat_salary() -> str:
    return "Зарплата в объявлении не указана — поэтому прошла, хотя у вас есть фильтр по деньгам"


def build_delete_confirm_text() -> str:
    return (
        "Удаление данных\n\n"
        "Будут удалены профиль поиска, история присланных вакансий "
        "и отметки о загрузках резюме.\n\n"
        "Действие необратимо. Чтобы снова пользоваться ботом, "
        "профиль придётся собрать заново."
    )


def build_delete_done_text() -> str:
    return "Данные удалены.\n\nВакансии больше не придут. Если захотите вернуться — /start."


def build_delete_cancelled_text() -> str:
    return "Удаление отменено, данные на месте."


def build_delete_nothing_text() -> str:
    return "Удалять нечего: данных о вас не сохранено."


def build_delete_keyboard_reset_text() -> str:
    return "Меню скрыто. Вернуть его можно командой /start."
