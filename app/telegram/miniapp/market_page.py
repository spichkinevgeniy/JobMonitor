"""Публичная страница рынка: вывод «терминала» и кэш среза.

Страница свёрстана моноширинным шрифтом, и колонки выравниваются
пробелами, поэтому строки собираются здесь, а не в шаблоне. Ширина
каждой строки не больше LINE_WIDTH: на телефоне вывод не должен уезжать
вбок.
"""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from app.application.services.market_stats_service import MarketSnapshot
from app.application.services.weekly_pulse_service import MSK
from app.domain.shared.value_objects import SpecializationType

LINE_WIDTH = 38
CACHE_TTL = timedelta(hours=1)

SPECIALIZATION_LABELS = {
    SpecializationType.BACKEND.value: "backend",
    SpecializationType.QA.value: "qa",
    SpecializationType.INFRASTRUCTURE_DEVOPS.value: "devops",
    SpecializationType.FRONTEND.value: "frontend",
    SpecializationType.GAMEDEV.value: "gamedev",
    SpecializationType.ANALYTICS.value: "аналитика",
    SpecializationType.UI_UX_DESIGN.value: "дизайн",
    SpecializationType.DATA_SCIENCE_ML.value: "ds/ml",
    SpecializationType.MOBILE.value: "mobile",
}
SKILL_LABELS = {
    "System Administration": "sysadmin",
    "QA Automation": "автотесты",
    "Manual QA": "ручное qa",
    "Machine Learning": "ml",
    "Data Analysis": "анализ",
    "Data Engineering": "data eng",
    "Unreal Engine": "unreal",
    "Design Systems": "design sys",
}
FORMAT_LABELS = {
    "REMOTE": "удалённо",
    "HYBRID": "гибрид",
    "ONSITE": "офис",
    "UNDEFINED": "не указано",
}

DIRECTION_BAR = 12
FORMAT_BAR = 20
SKILL_BAR = 16


@dataclass(frozen=True, slots=True)
class TerminalRow:
    text: str
    bar: str = ""
    # Недобранная часть шкалы, рисуется тусклым.
    rest: str = ""


def _label(mapping: dict[str, str], value: str, width: int) -> str:
    return mapping.get(value, value.lower())[:width]


def _money(value: int | None) -> str:
    return f"{round(value / 1000)}к" if value is not None else "-"


def _number(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def _bar(value: float, max_value: float, width: int) -> str:
    if value <= 0 or max_value <= 0:
        return ""
    return "█" * max(1, round(value / max_value * width))


def build_summary(snapshot: MarketSnapshot) -> list[tuple[str, str]]:
    updated = snapshot.generated_at.astimezone(MSK).strftime("%d.%m.%Y %H:%M")
    return [
        ("вакансий", _number(snapshot.vacancies)),
        ("с зарплатой", f"{snapshot.salary_percent}%"),
        ("каналов", _number(snapshot.channels)),
        ("в базе всего", _number(snapshot.all_time)),
        ("обновлено", f"{updated} мск"),
    ]


def build_direction_rows(snapshot: MarketSnapshot) -> list[TerminalRow]:
    rows = [TerminalRow(f"{'направление':<12}{'вак':>5}  {'зп':>4}")]
    top = max((item.vacancies for item in snapshot.directions), default=0)
    for item in snapshot.directions:
        name = _label(SPECIALIZATION_LABELS, item.specialization, 12)
        text = f"{name:<12}{item.vacancies:>5}  {_money(item.salary_median):>4}  "
        rows.append(TerminalRow(text, _bar(item.vacancies, top, DIRECTION_BAR)))
    return rows


def build_grade_rows(snapshot: MarketSnapshot) -> list[TerminalRow]:
    rows = [TerminalRow(f"{'':<10}{'junior':>7}{'middle':>7}{'senior':>7}{'lead':>6}")]
    for item in snapshot.grade_salaries:
        name = _label(SPECIALIZATION_LABELS, item.specialization, 10)
        *first, last = (_money(value) for value in item.medians)
        cells = "".join(f"{cell:>7}" for cell in first) + f"{last:>6}"
        rows.append(TerminalRow(f"{name:<10}{cells}"))
    return rows


def build_format_rows(snapshot: MarketSnapshot) -> list[TerminalRow]:
    rows = []
    for item in snapshot.formats:
        filled = _bar(item.percent, 100, FORMAT_BAR)
        rows.append(
            TerminalRow(
                f"{_label(FORMAT_LABELS, item.key, 11):<11}{item.percent:>3}%  ",
                filled,
                "░" * (FORMAT_BAR - len(filled)),
            )
        )
    return rows


def build_skill_rows(snapshot: MarketSnapshot) -> list[TerminalRow]:
    top = max((item.percent for item in snapshot.skills), default=0)
    return [
        TerminalRow(
            f"{_label(SKILL_LABELS, item.key, 11):<11}{item.percent:>3}%  ",
            _bar(item.percent, top, SKILL_BAR),
        )
        for item in snapshot.skills
    ]


def build_market_context(snapshot: MarketSnapshot) -> dict[str, Any]:
    return {
        "snapshot": snapshot,
        "summary": build_summary(snapshot),
        "direction_rows": build_direction_rows(snapshot),
        "grade_rows": build_grade_rows(snapshot),
        "format_rows": build_format_rows(snapshot),
        "skill_rows": build_skill_rows(snapshot),
        "vacancies_text": _number(snapshot.vacancies),
    }


class MarketSnapshotCache:
    """Срез пересчитывается раз в час: цифры за четыре недели меняются
    медленно, а страницу открывают и поисковые роботы."""

    def __init__(
        self, ttl: timedelta = CACHE_TTL, clock: Callable[[], datetime] | None = None
    ) -> None:
        self._ttl = ttl
        self._clock = clock or (lambda: datetime.now(UTC))
        self._snapshot: MarketSnapshot | None = None
        self._expires_at: datetime | None = None
        self._lock = asyncio.Lock()

    async def get(self, load: Callable[[], Awaitable[MarketSnapshot]]) -> MarketSnapshot:
        if self._fresh():
            assert self._snapshot is not None
            return self._snapshot
        async with self._lock:
            # Пока ждали замок, срез мог обновить соседний запрос.
            if self._fresh():
                assert self._snapshot is not None
                return self._snapshot
            self._snapshot = await load()
            self._expires_at = self._clock() + self._ttl
            return self._snapshot

    def _fresh(self) -> bool:
        return self._expires_at is not None and self._clock() < self._expires_at
