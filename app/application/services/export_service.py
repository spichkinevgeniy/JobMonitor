import json
import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.application.ports.unit_of_work import VacancyUnitOfWork
from app.domain.vacancy.entities import DispatchedVacancy


class ExportFormat(StrEnum):
    JSON = "json"
    MARKDOWN = "markdown"
    TXT = "txt"


_EXTENSIONS = {
    ExportFormat.JSON: "json",
    ExportFormat.MARKDOWN: "md",
    ExportFormat.TXT: "txt",
}

# Файл целиком собирается в памяти, поэтому размер выборки ограничен.
MAX_EXPORT_VACANCIES = 5000
MIN_FENCE_LENGTH = 3


@dataclass(frozen=True, slots=True)
class ExportFile:
    filename: str
    content: bytes
    count: int


class ExportService:
    """Собирает файл со всеми вакансиями, которые бот отправил пользователю.

    История ведётся с момента появления vacancy_dispatch_log — то, что
    рассылалось раньше, восстановить неоткуда.
    """

    def __init__(self, uow: VacancyUnitOfWork) -> None:
        self._uow = uow

    async def count_available(self, user_tg_id: int) -> tuple[int, datetime | None]:
        """Сколько вакансий доступно к выгрузке и с какого момента ведётся история."""
        async with self._uow:
            return await self._uow.vacancies.count_dispatched_for_user(user_tg_id)

    async def build(self, user_tg_id: int, export_format: ExportFormat) -> ExportFile | None:
        async with self._uow:
            dispatched = await self._uow.vacancies.find_dispatched_for_user(
                user_tg_id, limit=MAX_EXPORT_VACANCIES
            )

        if not dispatched:
            return None

        renderers = {
            ExportFormat.JSON: _render_json,
            ExportFormat.MARKDOWN: _render_markdown,
            ExportFormat.TXT: _render_txt,
        }
        content = renderers[export_format](dispatched)
        stamp = datetime.now().strftime("%Y-%m-%d")
        return ExportFile(
            filename=f"jobmonitor-vacancies-{stamp}.{_EXTENSIONS[export_format]}",
            content=content.encode("utf-8"),
            count=len(dispatched),
        )


def _as_dict(item: DispatchedVacancy) -> dict[str, object]:
    vacancy = item.vacancy
    return {
        "dispatched_at": item.dispatched_at.isoformat(),
        "created_at": vacancy.created_at.isoformat(),
        "specializations": sorted(entry.value for entry in vacancy.specializations.items),
        "skills": sorted(entry.value for entry in vacancy.skills.items),
        "grade": vacancy.grade.value,
        "experience_level": vacancy.experience_level.value,
        "work_format": vacancy.work_format.value,
        "company_type": vacancy.company_type.value,
        "salary_amount": vacancy.salary.amount,
        "salary_currency": vacancy.salary.currency.value if vacancy.salary.currency else None,
        "text": vacancy.text,
    }


def _render_json(items: list[DispatchedVacancy]) -> str:
    payload = {
        "exported_at": datetime.now().astimezone().isoformat(),
        "count": len(items),
        "vacancies": [_as_dict(item) for item in items],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _meta_lines(item: DispatchedVacancy) -> list[str]:
    vacancy = item.vacancy
    salary = "не указана"
    if vacancy.salary.amount is not None:
        currency = vacancy.salary.currency.value if vacancy.salary.currency else ""
        salary = f"от {vacancy.salary.amount} {currency}".strip()

    return [
        f"Получено: {item.dispatched_at:%d.%m.%Y %H:%M}",
        f"Специализации: {', '.join(sorted(e.value for e in vacancy.specializations.items))}",
        f"Скиллы: {', '.join(sorted(e.value for e in vacancy.skills.items))}",
        f"Грейд: {vacancy.grade.value}",
        f"Опыт: {vacancy.experience_level.value}",
        f"Формат: {vacancy.work_format.value}",
        f"Тип компании: {vacancy.company_type.value}",
        f"Зарплата: {salary}",
    ]


def _fence_for(text: str) -> str:
    """Текст вакансии — из чужого канала, в нём могут быть свои обратные кавычки."""
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    return "`" * max(MIN_FENCE_LENGTH, longest + 1)


def _render_markdown(items: list[DispatchedVacancy]) -> str:
    blocks = [
        f"# Вакансии из JobMonitor\n\nВсего: {len(items)}\n",
    ]
    for index, item in enumerate(items, start=1):
        meta = "\n".join(f"- {line}" for line in _meta_lines(item))
        text = item.vacancy.text
        fence = _fence_for(text)
        blocks.append(f"## Вакансия {index}\n\n{meta}\n\n{fence}\n{text}\n{fence}\n")
    return "\n".join(blocks)


def _render_txt(items: list[DispatchedVacancy]) -> str:
    separator = "-" * 60
    blocks = [f"Вакансии из JobMonitor. Всего: {len(items)}"]
    for index, item in enumerate(items, start=1):
        meta = "\n".join(_meta_lines(item))
        blocks.append(f"{separator}\nВакансия {index}\n{meta}\n\n{item.vacancy.text}")
    return "\n".join(blocks)
