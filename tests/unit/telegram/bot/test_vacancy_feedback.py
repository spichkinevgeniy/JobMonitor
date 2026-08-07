"""Кнопки под вакансией: объяснение и отметка «не подходит»."""

from app.telegram.bot.keyboards import (
    VACANCY_REJECT_BUTTON_TEXT,
    VACANCY_REJECT_CALLBACK_PREFIX,
    VACANCY_REJECTED_BUTTON_TEXT,
    VACANCY_UNDO_CALLBACK_PREFIX,
    VACANCY_WHY_BUTTON_TEXT,
    VACANCY_WHY_CALLBACK_PREFIX,
    get_vacancy_kb,
)
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
    def test_lists_matched_skills(self) -> None:
        text = build_vacancy_reason_text(FakeVacancy(), ["Python", "SQL"])

        assert "Python, SQL" in text
        assert "Backend" in text

    def test_explains_unstated_format(self) -> None:
        """Ради этой строки G и D выкатываются вместе."""
        text = build_vacancy_reason_text(FakeVacancy(work_format="UNDEFINED"), ["Python"])

        assert "Формат: в вакансии не указан" in text

    def test_explains_unstated_grade(self) -> None:
        text = build_vacancy_reason_text(FakeVacancy(grade="UNDEFINED"), ["Python"])

        assert "Грейд: в вакансии не указан" in text

    def test_survives_empty_match(self) -> None:
        text = build_vacancy_reason_text(FakeVacancy(), [])

        assert "Совпадений по навыкам нет" in text
