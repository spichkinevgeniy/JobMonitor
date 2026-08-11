"""Кнопки под вакансией: объяснение и отметка «не подходит»."""

from types import SimpleNamespace
from typing import Any

from app.telegram.bot.keyboards import (
    VACANCY_REJECT_BUTTON_TEXT,
    VACANCY_REJECT_CALLBACK_PREFIX,
    VACANCY_REJECTED_BUTTON_TEXT,
    VACANCY_UNDO_CALLBACK_PREFIX,
    VACANCY_WHY_BUTTON_TEXT,
    VACANCY_WHY_CALLBACK_PREFIX,
    get_vacancy_kb,
)
from app.telegram.bot.routers.vacancy_feedback import _caveats
from app.telegram.bot.views import build_vacancy_reason_text

VACANCY_ID = "0f8a1b2c-3d4e-5f60-7182-93a4b5c6d7e8"


class FakeVacancy:
    def __init__(self, grade: str = "MIDDLE", work_format: str = "REMOTE") -> None:
        self.specializations = ["Backend"]
        self.grade = grade
        self.work_format = work_format


class TestKeyboard:
    def test_both_buttons_present(self) -> None:
        texts = [b.text for row in get_vacancy_kb(VACANCY_ID).inline_keyboard for b in row]

        assert len(texts) == 2

    def test_callback_data_fits_telegram_limit(self) -> None:
        """Telegram режет callback_data на 64 байтах."""
        for row in get_vacancy_kb(VACANCY_ID).inline_keyboard:
            for button in row:
                assert len(button.callback_data.encode()) <= 64

    def test_callbacks_carry_the_vacancy_id(self) -> None:
        buttons = [b for row in get_vacancy_kb(VACANCY_ID).inline_keyboard for b in row]

        assert buttons[0].callback_data == f"{VACANCY_WHY_CALLBACK_PREFIX}{VACANCY_ID}"
        assert buttons[1].callback_data == f"{VACANCY_REJECT_CALLBACK_PREFIX}{VACANCY_ID}"


class TestKeyboardAfterRejection:
    def test_why_button_survives_rejection(self) -> None:
        """После отметки объяснение остаётся: человек всё ещё хочет понять."""
        rows = get_vacancy_kb(VACANCY_ID, rejected=True).inline_keyboard
        texts = [b.text for row in rows for b in row]

        assert VACANCY_WHY_BUTTON_TEXT in texts

    def test_reject_button_replaced_by_mark(self) -> None:
        rows = get_vacancy_kb(VACANCY_ID, rejected=True).inline_keyboard
        texts = [b.text for row in rows for b in row]

        assert VACANCY_REJECT_BUTTON_TEXT not in texts
        assert VACANCY_REJECTED_BUTTON_TEXT in texts

    def test_mark_undoes_the_choice_on_tap(self) -> None:
        """Промах по соседней кнопке иначе портит сигнал навсегда."""
        rows = get_vacancy_kb(VACANCY_ID, rejected=True).inline_keyboard
        mark = [b for row in rows for b in row if b.text == VACANCY_REJECTED_BUTTON_TEXT][0]

        assert mark.callback_data == f"{VACANCY_UNDO_CALLBACK_PREFIX}{VACANCY_ID}"

    def test_undo_callback_fits_telegram_limit(self) -> None:
        rows = get_vacancy_kb(VACANCY_ID, rejected=True).inline_keyboard

        for row in rows:
            for button in row:
                assert len(button.callback_data.encode()) <= 64


class TestReasonText:
    """Отвечает на «почему мне», а не пересказывает вакансию."""

    def test_shows_what_matched(self) -> None:
        text = build_vacancy_reason_text(["Backend"], ["Python", "SQL"], [])

        assert text == "Совпало с вашим профилем: Backend · Python · SQL"

    def test_no_vacancy_fields_in_text(self) -> None:
        """Грейд, формат и зарплату человек читает в самом объявлении."""
        text = build_vacancy_reason_text(["Backend"], ["Python"], [])

        for word in ("Грейд", "Формат", "Зарплата", "/settings"):
            assert word not in text

    def test_caveats_are_appended(self) -> None:
        text = build_vacancy_reason_text(["Backend"], ["Python"], ["первая", "вторая"])

        assert text.splitlines()[1:] == ["первая", "вторая"]

    def test_survives_missing_specializations(self) -> None:
        """У отправок до снимка специализаций их нет."""
        text = build_vacancy_reason_text([], ["Python"], [])

        assert text == "Совпало с вашим профилем: Python"

    def test_survives_empty_match(self) -> None:
        assert build_vacancy_reason_text([], [], []) == "Совпадений с профилем нет"


class TestCaveats:
    """Объясняем только то, что прошло вопреки настройке человека."""

    def _vacancy(self, **kwargs: object) -> Any:
        base = {
            "work_format": "REMOTE",
            "grade": "MIDDLE",
            "experience_level": "THREE_TO_SIX_YEARS",
            "salary_amount": 100,
        }
        return SimpleNamespace(**{**base, **kwargs})

    def _user(self, **kwargs: object) -> Any:
        base = {
            "filter_work_format_mode": "SOFT",
            "cv_work_format": None,
            "filter_grade_mode": "IGNORE",
            "cv_grade": None,
            "filter_experience_mode": "IGNORE",
            "cv_experience_level": None,
            "filter_salary_mode": "SOFT",
            "cv_salary_amount": None,
        }
        return SimpleNamespace(**{**base, **kwargs})

    def test_silent_when_everything_stated(self) -> None:
        assert _caveats(self._vacancy(), self._user()) == []

    def test_unstated_format_explained_for_strict_filter(self) -> None:
        caveats = _caveats(
            self._vacancy(work_format="UNDEFINED"),
            self._user(filter_work_format_mode="STRICT", cv_work_format="REMOTE"),
        )

        assert len(caveats) == 1
        assert "только удалёнка" in caveats[0]

    def test_unstated_format_silent_for_soft_filter(self) -> None:
        """Фильтр мягкий — вакансия прошла бы в любом случае, объяснять нечего."""
        caveats = _caveats(
            self._vacancy(work_format="UNDEFINED"),
            self._user(filter_work_format_mode="SOFT", cv_work_format="REMOTE"),
        )

        assert caveats == []

    def test_unstated_grade_explained(self) -> None:
        caveats = _caveats(
            self._vacancy(grade="UNDEFINED"),
            self._user(filter_grade_mode="UP_TO", cv_grade="MIDDLE"),
        )

        assert len(caveats) == 1

    def test_unstated_salary_explained(self) -> None:
        caveats = _caveats(
            self._vacancy(salary_amount=None),
            self._user(filter_salary_mode="STRICT", cv_salary_amount=200000),
        )

        assert len(caveats) == 1

    def test_several_caveats_at_once(self) -> None:
        caveats = _caveats(
            self._vacancy(work_format="UNDEFINED", salary_amount=None),
            self._user(
                filter_work_format_mode="STRICT",
                cv_work_format="REMOTE",
                filter_salary_mode="STRICT",
                cv_salary_amount=200000,
            ),
        )

        assert len(caveats) == 2


class TestSourceButton:
    """Заменяет шапку «Переслано из», которая была у пересылки."""

    def _buttons(self, **kwargs: object) -> list:
        kb = get_vacancy_kb(VACANCY_ID, **kwargs)  # type: ignore[arg-type]
        return [b for row in kb.inline_keyboard for b in row]

    def test_shows_channel_name_without_tapping(self) -> None:
        buttons = self._buttons(
            source_channel="@javascript_jobs",
            source_url="https://t.me/javascript_jobs/123",
        )

        assert any("Источник: @javascript_jobs" in b.text for b in buttons)

    def test_leads_to_the_exact_post(self) -> None:
        buttons = self._buttons(
            source_channel="@javascript_jobs",
            source_url="https://t.me/javascript_jobs/123",
        )
        source = [b for b in buttons if b.url][0]

        assert source.url == "https://t.me/javascript_jobs/123"

    def test_absent_without_source(self) -> None:
        assert all(b.url is None for b in self._buttons())

    def test_survives_rejection(self) -> None:
        """Иначе после «не подходит» источник пропадал бы."""
        buttons = self._buttons(
            rejected=True,
            source_channel="@javascript_jobs",
            source_url="https://t.me/javascript_jobs/123",
        )

        assert any(b.url for b in buttons)
        assert any(b.text == VACANCY_WHY_BUTTON_TEXT for b in buttons)
