"""Выводы по срезу для людей, поисковиков и ИИ."""

import json
import re
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.application.services.market_stats_service import (
    DirectionStat,
    GradeSalaryRow,
    MarketSnapshot,
    Share,
)
from app.telegram.miniapp.app import build_miniapp_app
from app.telegram.miniapp.deps import get_market_snapshot
from app.telegram.miniapp.market_facts import (
    build_findings,
    build_json_ld,
    build_llms_txt,
    human_date,
    weeks,
)

NOW = datetime(2026, 9, 28, 21, 30, tzinfo=UTC)  # 29 сентября по Москве


def snapshot(**overrides: object) -> MarketSnapshot:
    base: dict[str, object] = {
        "generated_at": NOW,
        "vacancies": 2251,
        "salary_percent": 36,
        "channels": 105,
        "all_time": 13448,
        "directions": [
            DirectionStat("Backend", 892, 235000),
            DirectionStat("QA", 291, 180000),
            DirectionStat("Infrastructure & DevOps", 288, 250000),
            DirectionStat("Data Science / ML", 137, 290000),
            DirectionStat("Mobile", 77, None),
        ],
        "grade_salaries": [GradeSalaryRow("Backend", (80000, 200000, 280000, 380000))],
        "formats": [
            Share("REMOTE", 55),
            Share("HYBRID", 18),
            Share("ONSITE", 16),
            Share("UNDEFINED", 12),
        ],
        "skills": [Share("Python", 23), Share("SQL", 19), Share("DevOps", 16), Share("Go", 9)],
    }
    base.update(overrides)
    return MarketSnapshot(**base)  # type: ignore[arg-type]


def plain(text: str) -> str:
    return text.replace(" ", " ")


class TestFindings:
    def test_date_in_moscow_time(self) -> None:
        """В 21:30 UTC в Москве уже следующий день."""
        assert human_date(NOW) == "29 сентября 2026"

    @pytest.mark.parametrize(
        ("days", "text"),
        [
            (7, "1 неделю"),
            (28, "4 недели"),
            (56, "8 недель"),
            (77, "11 недель"),
            (154, "22 недели"),
        ],
    )
    def test_weeks_agree_with_number(self, days: int, text: str) -> None:
        assert weeks(days) == text

    def test_headline_numbers(self) -> None:
        findings = plain(" ".join(build_findings(snapshot())))

        assert "на 29 сентября 2026" in findings
        assert "IT-вакансий: 2 251" in findings
        assert "в 36% вакансий" in findings

    def test_top_directions_in_order(self) -> None:
        findings = build_findings(snapshot())

        assert "направлениях backend, тестирование и DevOps." in findings[2]

    def test_highest_median(self) -> None:
        findings = plain(" ".join(build_findings(snapshot())))

        assert "Самая высокая медиана — в направлении Data Science и ML: 290 000 ₽." in findings

    def test_direction_without_salary_is_skipped(self) -> None:
        """У mobile выборка мала — в выводы о зарплатах он не попадает."""
        findings = " ".join(build_findings(snapshot()))

        assert "мобильная" not in findings

    def test_formats_and_skills(self) -> None:
        findings = build_findings(snapshot())

        assert "в 55% вакансий, гибрид — 18%, офис — 16%" in findings[-2]
        assert findings[-1] == "Чаще всего требуют Python, SQL и DevOps."

    def test_empty_market_says_only_the_count(self) -> None:
        empty = snapshot(vacancies=0, directions=[], skills=[], salary_percent=0)

        findings = build_findings(empty)

        assert len(findings) == 1
        assert findings[0].endswith("IT-вакансий: 0.")


class TestJsonLd:
    def test_valid_dataset(self) -> None:
        data = json.loads(build_json_ld(snapshot(), "https://jobmonitor-it.com/"))

        assert data["@type"] == "Dataset"
        assert data["url"] == "https://jobmonitor-it.com/"
        assert data["temporalCoverage"] == "2026-09-01/2026-09-29"
        assert "2 251" in plain(data["description"])

    def test_cannot_close_script_tag(self) -> None:
        """Текст из базы не должен закрыть <script> раньше времени."""
        hostile = snapshot(skills=[Share("</script><b>", 50)])

        assert "</" not in build_json_ld(hostile, "https://jobmonitor-it.com/")


class TestLlmsTxt:
    def test_structure(self) -> None:
        text = build_llms_txt(
            snapshot(), "https://jobmonitor-it.com", "https://t.me/JobMonitorIT_BOT"
        )

        assert text.startswith("# JobMonitor\n")
        assert "## Главное" in text
        assert "](https://jobmonitor-it.com/)" in text
        assert "](https://t.me/JobMonitorIT_BOT)" in text

    def test_plain_spaces(self) -> None:
        """В справке для ИИ неразрывные пробелы только мешают."""
        text = build_llms_txt(snapshot(), "https://jobmonitor-it.com", "https://t.me/x")

        assert " " not in text
        assert "IT-вакансий: 2 251" in text


@pytest.fixture
def client() -> TestClient:
    app = build_miniapp_app()

    async def fake_snapshot() -> MarketSnapshot:
        return snapshot()

    app.dependency_overrides[get_market_snapshot] = fake_snapshot
    return TestClient(app)


class TestRoutes:
    def test_page_has_findings_and_markup(self, client: TestClient) -> None:
        page = client.get("/").text

        assert "Чаще всего требуют Python, SQL и DevOps." in page
        match = re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.S)
        assert match is not None
        assert json.loads(match.group(1))["@type"] == "Dataset"

    def test_llms_txt_served(self, client: TestClient) -> None:
        response = client.get("/llms.txt")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")
        assert response.text.startswith("# JobMonitor")
