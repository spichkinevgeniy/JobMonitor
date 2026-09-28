"""Недельная сводка: текст, кнопки, окно отправки и рассылка без дублей."""

from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest
from aiogram.exceptions import TelegramForbiddenError
from aiogram.methods import SendMessage

from app.application.ports.observability_port import Feature
from app.application.services.stats_service import RejectionCount, SkillSuggestion
from app.application.services.weekly_pulse_service import SalaryMedian, WeeklyPulse, last_full_week
from app.bootstrap.weekly_pulse import in_send_window
from app.core.config import config
from app.domain.matching.entities import MatchRejectionReason
from app.domain.shared.value_objects import Grade
from app.domain.user.entities import User
from app.infrastructure.db.mappers.user import user_from_model, user_to_model
from app.telegram.bot import pulse_sender
from app.telegram.bot.keyboards import (
    PULSE_OFF_CALLBACK,
    PULSE_SETTINGS_CALLBACK,
    PULSE_TOGGLE_CALLBACK,
    get_pulse_kb,
    get_settings_menu_kb,
    with_source,
)
from app.telegram.bot.pulse_sender import PulseStatus, WeeklyPulseSender
from app.telegram.bot.views.pulse import (
    build_pulse_toggle_label,
    build_weekly_pulse_text,
    format_week_range,
)

WEEK = last_full_week(datetime(2026, 9, 30, 12, tzinfo=UTC))

PULSE = WeeklyPulse(
    week=WEEK,
    matched=23,
    matched_previous=20,
    sent=18,
    rejected=2,
    salary=SalaryMedian(specialization="Backend", grade=Grade.MIDDLE, amount=185_000, sample=64),
    skill=SkillSuggestion(skill="Kafka", unlocks=9),
    top_rejection=RejectionCount(reason=MatchRejectionReason.GRADE, count=12),
)


class TestText:
    def test_full_pulse(self) -> None:
        assert build_weekly_pulse_text(PULSE) == (
            "📊 Ваш рынок за неделю 21–27 сентября\n"
            "\n"
            "Подходящих вакансий: 23 (+15% к прошлой неделе)\n"
            "Отправили вам: 18, из них «не подходит»: 2\n"
            "\n"
            "💰 Медиана зарплаты Backend · Middle за 4 недели: 185 000 ₽ "
            "(по 64 вакансиям с зарплатой)\n"
            "🔥 Навык недели: Kafka — открыл бы ещё 9 вакансий\n"
            "🧹 Больше всего отсеял фильтр по грейду: 12 вакансий"
        )

    def test_empty_parts_are_left_out(self) -> None:
        pulse = replace(
            PULSE,
            matched=12,
            matched_previous=0,
            sent=0,
            salary=None,
            skill=None,
            top_rejection=None,
        )

        assert build_weekly_pulse_text(pulse) == (
            "📊 Ваш рынок за неделю 21–27 сентября\n\nПодходящих вакансий: 12"
        )

    @pytest.mark.parametrize(
        ("current", "previous", "expected"),
        [
            (20, 20, "(как на прошлой неделе)"),
            (16, 20, "(-20% к прошлой неделе)"),
            (40, 20, "(+100% к прошлой неделе)"),
        ],
    )
    def test_change_to_previous_week(self, current: int, previous: int, expected: str) -> None:
        text = build_weekly_pulse_text(replace(PULSE, matched=current, matched_previous=previous))

        assert expected in text

    def test_no_rejections_means_no_rejection_part(self) -> None:
        text = build_weekly_pulse_text(replace(PULSE, rejected=0))

        assert "Отправили вам: 18\n" in text

    def test_median_without_grade(self) -> None:
        salary = SalaryMedian(specialization="QA", grade=None, amount=180_000, sample=21)
        text = build_weekly_pulse_text(replace(PULSE, salary=salary))

        assert "Медиана зарплаты QA за 4 недели: 180 000 ₽ (по 21 вакансии с зарплатой)" in text

    @pytest.mark.parametrize(
        ("unlocks", "rejected", "unlocks_text", "rejected_text"),
        [
            (3, 1, "3 вакансии", "1 вакансия"),
            (21, 22, "21 вакансию", "22 вакансии"),
            (11, 14, "11 вакансий", "14 вакансий"),
        ],
    )
    def test_plural_forms(
        self, unlocks: int, rejected: int, unlocks_text: str, rejected_text: str
    ) -> None:
        text = build_weekly_pulse_text(
            replace(
                PULSE,
                skill=SkillSuggestion(skill="Kafka", unlocks=unlocks),
                top_rejection=RejectionCount(reason=MatchRejectionReason.SALARY, count=rejected),
            )
        )

        assert f"открыл бы ещё {unlocks_text}" in text
        assert f"фильтр по зарплате: {rejected_text}" in text

    def test_week_across_months(self) -> None:
        assert format_week_range(date(2026, 9, 28), date(2026, 10, 4)) == (
            "28 сентября – 4 октября"
        )


class TestKeyboards:
    def test_source_keeps_existing_query(self) -> None:
        assert with_source("https://bot.example/miniapp/stats?mode=stats", "pulse") == (
            "https://bot.example/miniapp/stats?mode=stats&source=pulse"
        )

    def test_pulse_buttons(self) -> None:
        rows = get_pulse_kb("https://bot.example/miniapp/stats").inline_keyboard
        buttons = [button for row in rows for button in row]

        assert buttons[0].web_app is not None
        assert buttons[0].web_app.url.endswith("source=pulse")
        assert [button.callback_data for button in buttons[1:]] == [
            PULSE_SETTINGS_CALLBACK,
            PULSE_OFF_CALLBACK,
        ]

    def test_no_stats_button_without_miniapp(self) -> None:
        buttons = [button for row in get_pulse_kb("").inline_keyboard for button in row]

        assert all(button.web_app is None for button in buttons)

    def test_settings_menu_has_pulse_toggle(self) -> None:
        markup = get_settings_menu_kb(
            specialty_and_skills_label="a",
            format_label="b",
            salary_label="c",
            level_label="d",
            specialty_url="https://x/1",
            format_url="https://x/2",
            salary_url="https://x/3",
            level_url="https://x/4",
            pulse_label=build_pulse_toggle_label(False),
        )
        toggle = [
            button
            for row in markup.inline_keyboard
            for button in row
            if button.callback_data == PULSE_TOGGLE_CALLBACK
        ]

        assert [button.text for button in toggle] == ["📊 Сводка по понедельникам: выкл"]


class TestSendWindow:
    @pytest.mark.parametrize(
        ("moment", "expected"),
        [
            (datetime(2026, 9, 28, 7, 0, tzinfo=UTC), True),  # понедельник 10:00 МСК
            (datetime(2026, 9, 28, 6, 59, tzinfo=UTC), False),  # 9:59
            (datetime(2026, 9, 28, 18, 59, tzinfo=UTC), True),  # 21:59
            (datetime(2026, 9, 28, 19, 0, tzinfo=UTC), False),  # 22:00
            (datetime(2026, 9, 29, 7, 0, tzinfo=UTC), False),  # вторник
        ],
    )
    def test_monday_from_ten_to_ten(self, moment: datetime, expected: bool) -> None:
        assert in_send_window(moment) is expected

    def test_flag_is_off_by_default_and_reaches_the_container(self) -> None:
        compose = Path("docker-compose.yml").read_text(encoding="utf-8")

        assert type(config).model_fields["WEEKLY_PULSE_ENABLED"].default is False
        assert "WEEKLY_PULSE_ENABLED: ${WEEKLY_PULSE_ENABLED" in compose


def test_mapper_keeps_pulse_flag() -> None:
    user = User.create(tg_id=1, cv_specializations_raw=["Backend"], cv_skills_raw=["Python"])
    user.pulse_enabled = False

    assert user_from_model(user_to_model(user)).pulse_enabled is False


class _Journal:
    """Общее состояние фейковых UoW: журнал переживает каждый `async with`."""

    def __init__(self, users: list[User]) -> None:
        self.users = users
        self.statuses: dict[tuple[int, date], str] = {}


class _FakeUsers:
    def __init__(self, journal: _Journal) -> None:
        self._journal = journal

    async def list_pulse_recipients(self) -> list[User]:
        return list(self._journal.users)

    async def claim_weekly_pulse(self, tg_id: int, week_start: date) -> bool:
        key = (tg_id, week_start)
        if key in self._journal.statuses:
            return False
        self._journal.statuses[key] = "pending"
        return True

    async def set_weekly_pulse_status(self, tg_id: int, week_start: date, status: str) -> None:
        self._journal.statuses[(tg_id, week_start)] = status


class _FakeUserUow:
    def __init__(self, journal: _Journal) -> None:
        self.users = _FakeUsers(journal)

    async def __aenter__(self) -> "_FakeUserUow":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


class _FakeBot:
    def __init__(self, forbidden: set[int] | None = None) -> None:
        self.sent: list[int] = []
        self._forbidden = forbidden or set()

    async def send_message(self, chat_id: int, text: str, **kwargs: Any) -> None:
        if chat_id in self._forbidden:
            raise TelegramForbiddenError(
                method=SendMessage(chat_id=chat_id, text=text),
                message="Forbidden: bot was blocked by the user",
            )
        self.sent.append(chat_id)


class TestSender:
    @pytest.fixture
    def features(self, monkeypatch: pytest.MonkeyPatch) -> list[Feature]:
        observed: list[Feature] = []
        monkeypatch.setattr(pulse_sender, "observe_feature", observed.append)
        return observed

    def _sender(
        self,
        monkeypatch: pytest.MonkeyPatch,
        matched: dict[int, int],
        bot: _FakeBot,
        deactivated: list[int] | None = None,
    ) -> tuple[WeeklyPulseSender, _Journal]:
        journal = _Journal(
            [
                User.create(tg_id=tg_id, cv_specializations_raw=["Backend"], cv_skills_raw=["Go"])
                for tg_id in matched
            ]
        )

        class _FakeService:
            def __init__(self, uow: object) -> None:
                pass

            async def build(self, user: User, week: object) -> WeeklyPulse:
                count = matched[user.tg_id.value]
                if count < 0:
                    raise RuntimeError("stats are broken")
                return replace(PULSE, matched=count)

        async def _deactivate(tg_id: int) -> None:
            if deactivated is not None:
                deactivated.append(tg_id)

        monkeypatch.setattr(pulse_sender, "WeeklyPulseService", _FakeService)
        sender = WeeklyPulseSender(
            bot=bot,  # type: ignore[arg-type]
            user_uow_factory=lambda: _FakeUserUow(journal),  # type: ignore[arg-type,return-value]
            vacancy_uow_factory=lambda: None,  # type: ignore[arg-type,return-value]
            stats_url="https://bot.example/miniapp/stats",
            deactivate=_deactivate,
            delay_seconds=0,
        )
        return sender, journal

    async def test_only_worth_sending_pulses_go_out(
        self, monkeypatch: pytest.MonkeyPatch, features: list[Feature]
    ) -> None:
        bot = _FakeBot()
        sender, journal = self._sender(monkeypatch, {1: 15, 2: 9}, bot)

        result = await sender.run(WEEK)

        assert bot.sent == [1]
        assert journal.statuses == {
            (1, WEEK.start_date): PulseStatus.SENT.value,
            (2, WEEK.start_date): PulseStatus.SKIPPED.value,
        }
        assert (result.sent, result.skipped) == (1, 1)
        assert features == [Feature.PULSE_SENT]

    async def test_rerun_after_restart_sends_nothing_twice(
        self, monkeypatch: pytest.MonkeyPatch, features: list[Feature]
    ) -> None:
        bot = _FakeBot()
        sender, _ = self._sender(monkeypatch, {1: 15, 2: 30}, bot)

        await sender.run(WEEK)
        second = await sender.run(WEEK)

        assert bot.sent == [1, 2]
        assert second.already_done == 2
        assert second.sent == 0

    async def test_blocked_user_is_deactivated(
        self, monkeypatch: pytest.MonkeyPatch, features: list[Feature]
    ) -> None:
        deactivated: list[int] = []
        bot = _FakeBot(forbidden={3})
        sender, journal = self._sender(monkeypatch, {3: 15}, bot, deactivated)

        await sender.run(WEEK)

        assert deactivated == [3]
        assert journal.statuses[(3, WEEK.start_date)] == PulseStatus.BLOCKED.value

    async def test_broken_stats_do_not_stop_the_run(
        self, monkeypatch: pytest.MonkeyPatch, features: list[Feature]
    ) -> None:
        bot = _FakeBot()
        sender, journal = self._sender(monkeypatch, {4: -1, 1: 15}, bot)

        result = await sender.run(WEEK)

        assert bot.sent == [1]
        assert journal.statuses[(4, WEEK.start_date)] == PulseStatus.FAILED.value
        assert result.failed == 1
