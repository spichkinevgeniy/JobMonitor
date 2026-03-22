from app.domain.shared.value_objects import ExperienceLevel, Grade
from app.domain.user.entities import User
from app.domain.user.value_objects import FilterMode
from app.telegram.bot.views.tracking_settings import format_salary, format_work_format

_GRADE_LABELS = {
    Grade.INTERN: "Intern",
    Grade.JUNIOR: "Junior",
    Grade.MIDDLE: "Middle",
    Grade.SENIOR: "Senior",
    Grade.LEAD: "Lead",
}
_EXPERIENCE_LABELS = {
    ExperienceLevel.NO_EXPERIENCE: "без опыта",
    ExperienceLevel.ONE_TO_THREE_YEARS: "1-3 года",
    ExperienceLevel.THREE_TO_SIX_YEARS: "3-6 лет",
    ExperienceLevel.SIX_PLUS_YEARS: "6+ лет",
}


def build_search_profile_text(user: User) -> str:
    specializations = _format_specializations(user)
    skills = _format_skills(user)

    salary = format_salary(user.cv_salary)
    grade = _format_grade(user)
    experience = _format_experience(user)
    work_format = format_work_format(user.cv_work_format)
    lines = [
        "👤 Профиль поиска",
        "",
        "Бот ориентируется на эти параметры:",
        _format_search_line("Направление(я)", specializations, bold_value=True),
        _format_search_line("Стек и навыки", skills, bold_value=True),
        "",
        "⚙️ Настройки вашего профиля:",
        _format_mode_filter_line(
            field_name="Зарплата",
            value=salary,
            mode=user.filter_salary_mode,
            any_value="Любая",
            soft_hint="Не учитываем 🟢",
            strict_hint="Скрываем всё, что меньше 🔴",
        ),
        _format_mode_filter_line(
            field_name="Грейд",
            value=grade,
            mode=user.filter_grade_mode,
            any_value="Любой",
            soft_hint="Не учитываем 🟢",
            strict_hint="Скрываем вакансии выше уровня 🔴",
        ),
        _format_mode_filter_line(
            field_name="Опыт",
            value=experience,
            mode=user.filter_experience_mode,
            any_value="Любой",
            soft_hint="Не учитываем 🟢",
            strict_hint="Скрываем вакансии с большим требованием 🔴",
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
        return f"• {field_name}: пока не указаны"

    rendered_value = f"<b>{value}</b>" if bold_value else value
    if suffix_emoji:
        return f"• {field_name}: {rendered_value} {suffix_emoji}"
    return f"• {field_name}: {rendered_value}"


def _format_specializations(user: User) -> str | None:
    values = sorted(item.value for item in user.cv_specializations.items)
    if not values:
        return None
    return ", ".join(values)


def _format_skills(user: User) -> str | None:
    values = sorted(item.value for item in user.cv_skills.items)
    if not values:
        return None
    return ", ".join(values)


def _format_grade(user: User) -> str | None:
    if user.cv_grade is None:
        return None
    return _GRADE_LABELS.get(user.cv_grade, user.cv_grade.value)


def _format_experience(user: User) -> str | None:
    if user.cv_experience_level is None:
        return None
    return _EXPERIENCE_LABELS.get(user.cv_experience_level, user.cv_experience_level.value)
