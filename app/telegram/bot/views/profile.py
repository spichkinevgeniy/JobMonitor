from app.domain.user.entities import User
from app.domain.user.value_objects import FilterMode
from app.telegram.bot.views.tracking_settings import format_salary, format_work_format


def build_search_profile_text(user: User) -> str:
    specializations = _format_specializations(user)
    languages = _format_languages(user)

    salary = format_salary(user.cv_salary)
    work_format = format_work_format(user.cv_work_format)

    lines = [
        "👤 Мой профиль поиска",
        "",
        "📍 Что мы ищем:",
        _format_search_line("Направление(я)", specializations, bold_value=True),
        _format_search_line("Основной язык(и)", languages, bold_value=True),
        "",
        "⚙️ Настройки фильтров:",
        _format_mode_filter_line(
            field_name="Зарплата",
            value=salary,
            mode=user.filter_salary_mode,
            any_value="Любая",
            soft_hint="Не учитываем 🟢",
            strict_hint="Скрываем всё, что меньше 🔴",
        ),
        _format_mode_filter_line(
            field_name="Формат",
            value=work_format,
            mode=user.filter_work_format_mode,
            any_value="Любой",
            soft_hint="Не учитываем 🟢",
            strict_hint="Только этот формат 🔴",
        ),
    ]
    return "\n".join(lines)


def _format_mode_filter_line(
    field_name: str,
    value: str | None,
    mode: FilterMode,
    any_value: str,
    soft_hint: str,
    strict_hint: str,
) -> str:
    if value is None:
        value = any_value
    hint = strict_hint if mode == FilterMode.STRICT else soft_hint
    return f"• {field_name}: {value} ({hint})"


def _format_search_line(
    field_name: str,
    value: str | None,
    suffix_emoji: str = "",
    bold_value: bool = False,
) -> str:
    if value is None:
        return f"• {field_name}: не найдено в резюме"

    rendered_value = f"<b>{value}</b>" if bold_value else value
    if suffix_emoji:
        return f"• {field_name}: {rendered_value} {suffix_emoji}"
    return f"• {field_name}: {rendered_value}"


def _format_specializations(user: User) -> str | None:
    values = sorted(item.value for item in user.cv_specializations.items)
    if not values:
        return None
    return ", ".join(values)


def _format_languages(user: User) -> str | None:
    values = sorted(item.value for item in user.cv_primary_languages.items)
    if not values:
        return None
    return ", ".join(values)

