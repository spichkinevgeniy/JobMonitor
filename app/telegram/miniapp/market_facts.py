"""Выводы по срезу рынка обычными словами: для людей, поисковиков и ИИ.

Таблицы на странице читают люди, а поисковики и ИИ-ассистенты цитируют
готовые утверждения. Отсюда их берут абзац на главной, разметка
schema.org и /llms.txt, поэтому цифры везде совпадают.

Фразы построены так, чтобы не согласовывать слова с числом:
«опубликовано IT-вакансий: 2 251» верно при любом числе, а
«вышла 2 251 вакансия» — только при некоторых.
"""

import json
from datetime import datetime

from app.application.services.market_stats_service import (
    COUNT_WINDOW,
    MIN_SALARY_SAMPLE,
    SALARY_WINDOW,
    MarketSnapshot,
)
from app.application.services.weekly_pulse_service import MSK
from app.domain.shared.value_objects import SpecializationType

PROSE_LABELS = {
    SpecializationType.BACKEND.value: "backend",
    SpecializationType.QA.value: "тестирование",
    SpecializationType.INFRASTRUCTURE_DEVOPS.value: "DevOps",
    SpecializationType.FRONTEND.value: "frontend",
    SpecializationType.GAMEDEV.value: "геймдев",
    SpecializationType.ANALYTICS.value: "аналитика",
    SpecializationType.UI_UX_DESIGN.value: "дизайн",
    SpecializationType.DATA_SCIENCE_ML.value: "Data Science и ML",
    SpecializationType.MOBILE.value: "мобильная разработка",
}
GENITIVE_MONTHS = (
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
)
NBSP = " "


def human_date(moment: datetime) -> str:
    local = moment.astimezone(MSK)
    return f"{local.day} {GENITIVE_MONTHS[local.month - 1]} {local.year}"


def weeks(days: int) -> str:
    count = days // 7
    if count % 10 == 1 and count % 100 != 11:
        word = "неделю"
    elif count % 10 in (2, 3, 4) and count % 100 not in (12, 13, 14):
        word = "недели"
    else:
        word = "недель"
    return f"{count} {word}"


def _number(value: int) -> str:
    return f"{value:,}".replace(",", NBSP)


def _rub(value: int) -> str:
    return f"{_number(value)}{NBSP}₽"


def _join(items: list[str]) -> str:
    if len(items) <= 1:
        return "".join(items)
    return f"{', '.join(items[:-1])} и {items[-1]}"


def _label(specialization: str) -> str:
    return PROSE_LABELS.get(specialization, specialization)


def build_findings(snapshot: MarketSnapshot) -> list[str]:
    findings = [
        f"По данным JobMonitor на {human_date(snapshot.generated_at)}, за последние "
        f"{weeks(COUNT_WINDOW.days)} в Telegram-каналах опубликовано IT-вакансий: "
        f"{_number(snapshot.vacancies)}."
    ]
    if not snapshot.vacancies:
        return findings

    findings.append(f"Зарплату указывают в {snapshot.salary_percent}% вакансий.")

    top = [_label(item.specialization) for item in snapshot.directions[:3]]
    if top:
        findings.append(f"Больше всего вакансий в направлениях {_join(top)}.")

    paid = [item for item in snapshot.directions if item.salary_median is not None]
    if paid:
        parts = [
            f"{_label(item.specialization)} — {_rub(item.salary_median or 0)}" for item in paid[:3]
        ]
        findings.append(
            f"Медианная зарплата «от» за {weeks(SALARY_WINDOW.days)}: {', '.join(parts)}."
        )
        best = max(paid, key=lambda item: item.salary_median or 0)
        findings.append(
            f"Самая высокая медиана — в направлении {_label(best.specialization)}: "
            f"{_rub(best.salary_median or 0)}."
        )

    shares = {item.key: item.percent for item in snapshot.formats}
    findings.append(
        f"Удалённо можно работать в {shares.get('REMOTE', 0)}% вакансий, "
        f"гибрид — {shares.get('HYBRID', 0)}%, офис — {shares.get('ONSITE', 0)}%."
    )

    skills = [item.key for item in snapshot.skills[:3]]
    if skills:
        findings.append(f"Чаще всего требуют {_join(skills)}.")
    return findings


def build_json_ld(snapshot: MarketSnapshot, url: str) -> str:
    """Описание страницы для машин: что за данные, за какой период и когда обновлены."""
    start = (snapshot.generated_at - COUNT_WINDOW).astimezone(MSK).date()
    end = snapshot.generated_at.astimezone(MSK).date()
    data = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": "Рынок IT-вакансий в Telegram",
        "description": " ".join(build_findings(snapshot)),
        "url": url,
        "inLanguage": "ru",
        "isAccessibleForFree": True,
        "dateModified": snapshot.generated_at.isoformat(),
        "temporalCoverage": f"{start.isoformat()}/{end.isoformat()}",
        "creator": {"@type": "Organization", "name": "JobMonitor", "url": url},
        "keywords": [
            "IT-вакансии",
            "зарплаты в IT",
            "Telegram",
            "рынок труда",
            "удалённая работа",
        ],
        "variableMeasured": [
            "число вакансий по направлениям",
            "медианная зарплата по направлениям и грейдам",
            "доля удалённых вакансий",
            "частота навыков в вакансиях",
        ],
    }
    # Внутри <script> строка «</» закрыла бы тег раньше времени.
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def build_llms_txt(snapshot: MarketSnapshot, origin: str, bot_url: str) -> str:
    """Справка о сайте для ИИ-ассистентов в формате llms.txt."""
    updated = snapshot.generated_at.astimezone(MSK).strftime("%H:%M")
    lines = [
        "# JobMonitor",
        "",
        "> Срез рынка IT-вакансий из Telegram-каналов и Telegram-бот, который присылает "
        "вакансии под стек, грейд и зарплату.",
        "",
        f"Данные обновляются каждый час. Последнее обновление: "
        f"{human_date(snapshot.generated_at)}, {updated} по Москве.",
        "",
        "## Главное",
        "",
        *(f"- {item}" for item in build_findings(snapshot)),
        "",
        "## Страницы",
        "",
        f"- [Рынок IT-вакансий в Telegram]({origin}/): вакансии и медианные зарплаты "
        "по направлениям и грейдам, формат работы, самые частые навыки.",
        f"- [Бот JobMonitor]({bot_url}): присылает подходящие вакансии из Telegram-каналов.",
        "",
        "## Как считаются цифры",
        "",
        f"- Вакансии, форматы и навыки — за последние {weeks(COUNT_WINDOW.days)}, "
        f"зарплаты — за {weeks(SALARY_WINDOW.days)}.",
        "- Зарплата — нижняя граница вилки в рублях. Медиана не показывается, "
        f"если вакансий с зарплатой меньше {MIN_SALARY_SAMPLE}.",
        "- Одинаковые тексты из разных каналов считаются одной вакансией.",
        "- Направление, грейд и навыки размечаются автоматически и иногда ошибаются.",
    ]
    return "\n".join(lines).replace(NBSP, " ") + "\n"
