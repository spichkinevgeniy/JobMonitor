from app.domain.shared.value_objects import Salary, WorkFormat


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
    return f"от {amount} ₽"
