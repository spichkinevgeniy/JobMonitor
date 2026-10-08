"""Публичная страница рынка: вывод «терминала», кэш и сама страница."""

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.application.ports.observability_port import Feature
from app.application.services.market_stats_service import (
    DirectionStat,
    GradeSalaryRow,
    MarketSnapshot,
    Share,
)
from app.telegram.miniapp.app import build_miniapp_app
from app.telegram.miniapp.deps import get_market_snapshot
from app.telegram.miniapp.market_page import (
    LINE_WIDTH,
    MarketSnapshotCache,
    build_market_context,
)
from app.telegram.miniapp.routes import public as public_routes

NOW = datetime(2026, 9, 28, 19, 49, tzinfo=UTC)
BROWSER = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
)
VIEW_URL = "/miniapp/api/market/view"


def snapshot(**overrides: object) -> MarketSnapshot:
    base: dict[str, object] = {
        "generated_at": NOW,
        "vacancies": 2251,
        "salary_percent": 36,
        "channels": 105,
        "all_time": 13448,
        "directions": [
            DirectionStat("Backend", 892, 235000),
            DirectionStat("Mobile", 77, None),
        ],
        "grade_salaries": [GradeSalaryRow("Backend", (80000, 200000, 280000, 380000))],
        "formats": [
            Share("REMOTE", 55),
            Share("HYBRID", 18),
            Share("ONSITE", 16),
            Share("UNDEFINED", 12),
        ],
        "skills": [Share("Python", 23), Share("QA Automation", 7)],
    }
    base.update(overrides)
    return MarketSnapshot(**base)  # type: ignore[arg-type]


def all_lines(context: dict[str, object]) -> list[str]:
    lines = [f"{key:<14}{value}" for key, value in context["summary"]]  # type: ignore[attr-defined]
    for name in ("direction_rows", "grade_rows", "format_rows", "skill_rows"):
        lines += [row.text + row.bar + row.rest for row in context[name]]  # type: ignore[attr-defined]
    return lines


class TestTerminalRows:
    def test_fits_phone_width(self) -> None:
        lines = all_lines(build_market_context(snapshot()))

        assert max(len(line) for line in lines) <= LINE_WIDTH

    def test_fits_phone_width_on_extremes(self) -> None:
        """Длинные названия, большие числа и зарплата за миллион."""
        extreme = snapshot(
            vacancies=123456,
            all_time=9876543,
            directions=[
                DirectionStat("Infrastructure & DevOps", 99999, 1250000),
                DirectionStat("Some Very Long New Specialization", 1, None),
            ],
            grade_salaries=[GradeSalaryRow("Some Very Long New Specialization", (1250000,) * 4)],
            skills=[Share("Some Extremely Long Skill Name", 100)],
        )

        lines = all_lines(build_market_context(extreme))

        assert max(len(line) for line in lines) <= LINE_WIDTH

    def test_small_sample_shows_dash(self) -> None:
        rows = build_market_context(snapshot())["direction_rows"]

        assert rows[2].text.split()[:3] == ["mobile", "77", "-"]

    def test_money_in_thousands(self) -> None:
        rows = build_market_context(snapshot())["grade_rows"]

        assert rows[1].text.split() == ["backend", "80к", "200к", "280к", "380к"]

    def test_russian_labels(self) -> None:
        context = build_market_context(snapshot())

        assert context["format_rows"][0].text.startswith("удалённо")
        assert context["skill_rows"][1].text.startswith("автотесты")

    def test_format_scale_is_full_width(self) -> None:
        row = build_market_context(snapshot())["format_rows"][0]

        assert len(row.bar + row.rest) == 20

    def test_updated_in_moscow_time(self) -> None:
        summary = dict(build_market_context(snapshot())["summary"])

        assert summary["обновлено"] == "28.09.2026 22:49 мск"


class TestCache:
    @pytest.mark.asyncio
    async def test_loads_once_within_ttl(self) -> None:
        now = [NOW]
        cache = MarketSnapshotCache(ttl=timedelta(hours=1), clock=lambda: now[0])
        loads = []

        async def load() -> MarketSnapshot:
            loads.append(1)
            return snapshot()

        await cache.get(load)
        now[0] += timedelta(minutes=59)
        await cache.get(load)

        assert len(loads) == 1

    @pytest.mark.asyncio
    async def test_reloads_after_ttl(self) -> None:
        now = [NOW]
        cache = MarketSnapshotCache(ttl=timedelta(hours=1), clock=lambda: now[0])
        loads = []

        async def load() -> MarketSnapshot:
            loads.append(1)
            return snapshot()

        await cache.get(load)
        now[0] += timedelta(hours=1, seconds=1)
        await cache.get(load)

        assert len(loads) == 2

    @pytest.mark.asyncio
    async def test_parallel_requests_hit_database_once(self) -> None:
        """Робот поисковика и живой человек пришли одновременно на холодный кэш."""
        cache = MarketSnapshotCache(clock=lambda: NOW)
        loads = []

        async def load() -> MarketSnapshot:
            loads.append(1)
            await asyncio.sleep(0)
            return snapshot()

        await asyncio.gather(*(cache.get(load) for _ in range(5)))

        assert len(loads) == 1


@pytest.fixture
def client() -> TestClient:
    app = build_miniapp_app()

    async def fake_snapshot() -> MarketSnapshot:
        return snapshot()

    app.dependency_overrides[get_market_snapshot] = fake_snapshot
    return TestClient(app)


class TestPage:
    def test_available_without_telegram_auth(self, client: TestClient) -> None:
        assert client.get("/").status_code == 200

    def test_renders_numbers(self, client: TestClient) -> None:
        page = client.get("/").text

        assert "2 251" in page
        assert "235к" in page
        assert "{{" not in page

    def test_links_to_bot(self, client: TestClient) -> None:
        assert "https://t.me/JobMonitorIT_BOT" in client.get("/").text

    def test_robots_hides_miniapp(self, client: TestClient) -> None:
        robots = client.get("/robots.txt").text

        assert "Disallow: /miniapp" in robots
        assert "/sitemap.xml" in robots

    def test_sitemap_lists_public_pages(self, client: TestClient) -> None:
        response = client.get("/sitemap.xml")

        assert response.headers["content-type"].startswith("application/xml")
        assert "/</loc>" in response.text
        assert "/privacy</loc>" in response.text


@pytest.fixture
def views(monkeypatch: pytest.MonkeyPatch) -> list[Feature]:
    seen: list[Feature] = []
    monkeypatch.setattr(public_routes, "observe_feature", seen.append)
    return seen


class TestHonestViews:
    """Просмотр засчитывает браузер, а не каждый запрос страницы: в запросах
    роботов было в разы больше, чем людей."""

    def test_page_request_alone_is_not_a_view(
        self, client: TestClient, views: list[Feature]
    ) -> None:
        client.get("/", headers={"user-agent": BROWSER})

        assert views == []

    def test_page_sends_the_signal(self, client: TestClient) -> None:
        assert "js/market-view.js" in client.get("/").text

    def test_signal_from_browser_counts(self, client: TestClient, views: list[Feature]) -> None:
        response = client.post(
            VIEW_URL, headers={"user-agent": BROWSER, "sec-fetch-site": "same-origin"}
        )

        assert response.status_code == 204
        assert views == [Feature.MARKET_VIEW]

    def test_old_browser_without_fetch_metadata_counts_by_origin(
        self, client: TestClient, views: list[Feature]
    ) -> None:
        client.post(VIEW_URL, headers={"user-agent": BROWSER, "origin": str(client.base_url)})

        assert views == [Feature.MARKET_VIEW]

    @pytest.mark.parametrize(
        "user_agent",
        [
            "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 HeadlessChrome/120.0 Safari/537.36",
            "TelegramBot (like TwitterBot)",
            "curl/8.4.0",
            "python-requests/2.32.3",
        ],
    )
    def test_robots_do_not_count(
        self, client: TestClient, views: list[Feature], user_agent: str
    ) -> None:
        client.post(VIEW_URL, headers={"user-agent": user_agent, "sec-fetch-site": "same-origin"})

        assert views == []

    def test_signal_from_another_site_does_not_count(
        self, client: TestClient, views: list[Feature]
    ) -> None:
        client.post(
            VIEW_URL,
            headers={
                "user-agent": BROWSER,
                "sec-fetch-site": "cross-site",
                "origin": "https://example.com",
            },
        )

        assert views == []
