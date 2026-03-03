from app.domain.shared.value_objects import Salary, WorkFormat
from app.domain.user.entities import User

EXPERIENCE_STEP = "experience"
SALARY_STEP = "salary"
FORMAT_STEP = "format"


def format_work_format(work_format: WorkFormat | None) -> str | None:
    if work_format is None:
        return None

    labels = {
        WorkFormat.REMOTE: "Удаленка",
        WorkFormat.HYBRID: "Гибрид",
        WorkFormat.ONSITE: "Офис",
    }
    return labels.get(work_format)


def format_salary(salary: Salary | None) -> str | None:
    if salary is None or salary.amount is None:
        return None

    amount = f"{salary.amount:,}".replace(",", " ")
    if salary.currency is None:
        return f"от {amount} (валюта не указана)"

    symbols = {
        "RUB": "₽",
        "USD": "$",
        "EUR": "€",
    }
    suffix = symbols.get(salary.currency.value, salary.currency.value)
    return f"от {amount} {suffix}"


def format_experience(months: int | None) -> str | None:
    if months is None or months <= 0:
        return None

    years = months // 12
    rem_months = months % 12
    parts: list[str] = []

    if years > 0:
        parts.append(f"{years} {_plural_ru(years, ('год', 'года', 'лет'))}")
    if rem_months > 0:
        parts.append(f"{rem_months} {_plural_ru(rem_months, ('месяц', 'месяца', 'месяцев'))}")

    return " и ".join(parts)


def build_tracking_intro_and_available_steps(user: User) -> tuple[str, list[str]]:
    work_format_text = format_work_format(user.cv_work_format)
    salary_text = format_salary(user.cv_salary)
    experience_text = format_experience(user.cv_experience_months)

    lines = [
        "🎯 Точная настройка отслеживания",
        "",
        "Настройте, как бот должен отбирать для вас вакансии.",
        "",
        (
            "Основной поиск всегда идет по вашим специализациям и технологиям. "
            "Ниже вы можете включить дополнительные фильтры, чтобы отсеять неподходящие "
            "предложения."
        ),
        "",
        "Ваши данные из резюме:",
    ]

    if work_format_text is None:
        lines.append("• 🏠 Формат: не найден в резюме ")
    else:
        lines.append(f"• 🏠 Формат: {work_format_text}")

    if salary_text is None:
        lines.append("• 💰 Зарплата: не указана (или не найдена)")
    else:
        lines.append(f"• 💰 Зарплата: {salary_text}")

    if experience_text is None:
        lines.append("• ⏳ Опыт: не найден в резюме ")
    else:
        lines.append(f"• ⏳ Опыт: {experience_text}")

    lines.append("")
    lines.append(
        "Если вы активируете эти фильтры, бот перестанет присылать вакансии, которые "
        "не соответствуют вашим ожиданиям."
    )
    lines.append(
        "🚀 Включите нужные фильтры, чтобы получать меньше шума и больше подходящих вакансий."
    )

    available_steps: list[str] = []
    available_steps.append(EXPERIENCE_STEP)
    if salary_text is not None:
        available_steps.append(SALARY_STEP)
    if work_format_text is not None:
        available_steps.append(FORMAT_STEP)

    return "\n".join(lines), available_steps


def _plural_ru(value: int, forms: tuple[str, str, str]) -> str:
    mod10 = value % 10
    mod100 = value % 100
    if mod10 == 1 and mod100 != 11:
        return forms[0]
    if 2 <= mod10 <= 4 and not 12 <= mod100 <= 14:
        return forms[1]
    return forms[2]
