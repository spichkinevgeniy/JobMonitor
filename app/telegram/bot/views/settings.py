import posixpath
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit

from app.core.config import config
from app.domain.shared.value_objects import ExperienceLevel, Grade
from app.domain.user.entities import User
from app.domain.user.value_objects import FilterMode, LevelFilterMode
from app.telegram.bot.views.copy import build_settings_intro_text
from app.telegram.bot.views.tracking_settings import format_work_format

SETTINGS_ENTRY_SPECIALTY = "specialty"
SETTINGS_ENTRY_FORMAT = "format"
SETTINGS_ENTRY_SALARY = "salary"
SETTINGS_ENTRY_LEVEL = "level"

ENTRY_TO_PAGE = {
    SETTINGS_ENTRY_SPECIALTY: "specialty",
    SETTINGS_ENTRY_FORMAT: "format",
    SETTINGS_ENTRY_SALARY: "salary",
    SETTINGS_ENTRY_LEVEL: "level",
}

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


@dataclass(frozen=True, slots=True)
class SettingsMenuView:
    specialty_label: str
    format_label: str
    salary_label: str
    level_label: str
    specialty_url: str
    format_url: str
    salary_url: str
    level_url: str


def build_settings_menu_view(user: User) -> SettingsMenuView:
    specs_count = len(user.cv_specializations.items)
    skills_count = len(user.cv_skills.items)
    selected_count = specs_count + skills_count

    specialty_label = f"Направления и стек [Выбрано: {selected_count}]"
    format_label = f"Формат работы [{_format_label(user)}]"
    salary_label = f"Зарплатный ориентир [{_salary_label(user)}]"
    level_label = f"Грейд и опыт [{_level_label(user)}]"

    specialty_url = _build_entry_url(SETTINGS_ENTRY_SPECIALTY)
    format_url = _build_entry_url(SETTINGS_ENTRY_FORMAT)
    salary_url = _build_entry_url(SETTINGS_ENTRY_SALARY)
    level_url = _build_entry_url(SETTINGS_ENTRY_LEVEL)

    return SettingsMenuView(
        specialty_label=specialty_label,
        format_label=format_label,
        salary_label=salary_label,
        level_label=level_label,
        specialty_url=specialty_url,
        format_url=format_url,
        salary_url=salary_url,
        level_url=level_url,
    )


def build_settings_menu_text() -> str:
    return build_settings_intro_text()


def _format_label(user: User) -> str:
    if user.filter_work_format_mode != FilterMode.STRICT or user.cv_work_format is None:
        return "Любой"

    rendered = format_work_format(user.cv_work_format)
    return rendered or "Любой"


def _salary_label(user: User) -> str:
    if user.filter_salary_mode != FilterMode.STRICT or user.cv_salary is None:
        return "Любая"
    if user.cv_salary.amount is None:
        return "Любая"

    amount = f"{user.cv_salary.amount:,}".replace(",", " ")
    return f"от {amount} RUB/мес"


def _level_label(user: User) -> str:
    parts: list[str] = []
    grade_part = _single_level_label(
        mode=user.filter_grade_mode,
        value=_GRADE_LABELS.get(user.cv_grade, user.cv_grade.value) if user.cv_grade else None,
    )
    experience_part = _single_level_label(
        mode=user.filter_experience_mode,
        value=(
            _EXPERIENCE_LABELS.get(user.cv_experience_level, user.cv_experience_level.value)
            if user.cv_experience_level
            else None
        ),
    )
    if grade_part:
        parts.append(grade_part)
    if experience_part:
        parts.append(experience_part)
    return " · ".join(parts) if parts else "не учитывать"


def _single_level_label(mode: LevelFilterMode, value: str | None) -> str | None:
    if mode == LevelFilterMode.IGNORE or value is None:
        return None
    if mode == LevelFilterMode.UP_TO:
        return f"до {value}"
    return f"точно {value}"


def _build_entry_url(entry: str) -> str:
    raw_base = config.MINI_APP_BASE_URL.strip()
    if not raw_base:
        return ""

    parsed = urlsplit(raw_base)
    page = ENTRY_TO_PAGE.get(entry)
    if page is None:
        return ""

    base_dir = _resolve_base_dir(parsed.path)
    target_path = posixpath.join(base_dir, "miniapp", page)
    if not target_path.startswith("/"):
        target_path = f"/{target_path}"

    return urlunsplit((parsed.scheme, parsed.netloc, target_path, "", parsed.fragment))


def _resolve_base_dir(raw_path: str) -> str:
    base_dir = raw_path or "/"
    if "." in posixpath.basename(base_dir):
        base_dir = posixpath.dirname(base_dir)
    return base_dir or "/"
