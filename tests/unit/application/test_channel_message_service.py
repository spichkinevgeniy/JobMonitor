"""Путь сообщения из канала: какие исходы гасятся здесь, а какие — сбой."""

from typing import Any

import pytest

from app.application.dto import InfoRawVacancy, OutVacancyParse
from app.application.dto.resume_dto import SkillWithEvidence
from app.application.ports.llm_port import LLMUnavailableError
from app.application.ports.observability_port import SkipReason
from app.application.services.channel_message_service import ChannelMessageService
from app.domain.shared.value_objects import SkillType, SpecializationType
from app.domain.vacancy.entities import Vacancy
from app.domain.vacancy.exceptions import DuplicateVacancyError

MESSAGE = InfoRawVacancy(
    text="Ищем Python-разработчика в платёжную команду. Удалённо, от 300 000 ₽. @hr",
    mirror_chat_id=-100,
    mirror_message_id=7,
    chat_id=-200,
    message_id=5,
    source_channel="@jobs",
)
VACANCY = OutVacancyParse(
    is_vacancy=True,
    specializations=[SpecializationType.BACKEND],
    skills=[SkillWithEvidence(skill=SkillType.PYTHON, evidence="Python")],
)


class FakeExtractor:
    def __init__(self, result: OutVacancyParse = VACANCY, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.calls = 0

    async def parse_vacancy(self, text: str) -> OutVacancyParse:
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.result


class FakeVacancies:
    def __init__(self, exists: bool = False) -> None:
        self.exists = exists
        self.saved: list[Vacancy] = []

    async def exists_by_content_hash(self, content_hash: Any) -> bool:
        return self.exists

    async def upsert(self, vacancy: Vacancy) -> None:
        self.saved.append(vacancy)


class FakeVacancyUoW:
    """Сохранение падает на commit, как настоящая уникальность в базе."""

    def __init__(self, repo: FakeVacancies, save_error: Exception | None) -> None:
        self._repo = repo
        self._save_error = save_error

    @property
    def vacancies(self) -> FakeVacancies:
        return self._repo

    async def __aenter__(self) -> "FakeVacancyUoW":
        return self

    async def __aexit__(self, exc_type: Any, *args: Any) -> None:
        if exc_type is None:
            await self.commit()

    async def commit(self) -> None:
        if self._save_error is not None and self._repo.saved:
            raise self._save_error

    async def rollback(self) -> None:
        return None


class FakeMatchingVacancies:
    def __init__(self) -> None:
        self.requested: list[Any] = []

    async def get_by_id(self, vacancy_id: Any) -> None:
        # Вакансии «нет» — подбор на этом заканчивается, но запрос виден.
        self.requested.append(vacancy_id)


class FakeMatchingUoW:
    def __init__(self, vacancies: FakeMatchingVacancies) -> None:
        self.vacancies = vacancies
        self.users = None

    async def __aenter__(self) -> "FakeMatchingUoW":
        return self

    async def __aexit__(self, *args: Any) -> None:
        return None


class ObservabilitySpy:
    def __init__(self) -> None:
        self.skipped: list[SkipReason] = []

    def observe_message_skipped(self, reason: SkipReason) -> None:
        self.skipped.append(reason)

    def observe_not_vacancy_detected(self, count: int = 1) -> None:
        return None

    def observe_vacancy_collected(self, count: int = 1) -> None:
        return None


class Setup:
    def __init__(
        self,
        extractor: FakeExtractor | None = None,
        exists: bool = False,
        save_error: Exception | None = None,
    ) -> None:
        self.extractor = extractor or FakeExtractor()
        self.vacancies = FakeVacancies(exists)
        self.matching = FakeMatchingVacancies()
        self.observability = ObservabilitySpy()
        self.service = ChannelMessageService(
            vacancy_uow=lambda: FakeVacancyUoW(self.vacancies, save_error),  # type: ignore[arg-type,return-value]
            matching_uow=lambda: FakeMatchingUoW(self.matching),  # type: ignore[arg-type,return-value]
            extractor=self.extractor,
            notifications=None,  # type: ignore[arg-type]  # до рассылки не доходит
            observability=self.observability,  # type: ignore[arg-type]
        )


async def test_vacancy_is_saved_and_matched() -> None:
    setup = Setup()

    await setup.service.process(MESSAGE)

    assert len(setup.vacancies.saved) == 1
    assert setup.matching.requested == [setup.vacancies.saved[0].id]
    assert setup.observability.skipped == []


async def test_known_text_never_reaches_the_model() -> None:
    setup = Setup(exists=True)

    await setup.service.process(MESSAGE)

    assert setup.extractor.calls == 0
    assert setup.observability.skipped == [SkipReason.DUPLICATE]


async def test_not_a_vacancy_is_neither_saved_nor_matched() -> None:
    setup = Setup(extractor=FakeExtractor(OutVacancyParse(is_vacancy=False)))

    await setup.service.process(MESSAGE)

    assert setup.vacancies.saved == []
    assert setup.matching.requested == []
    assert setup.observability.skipped == [SkipReason.NOT_VACANCY]


async def test_duplicate_caught_on_save_is_still_a_duplicate() -> None:
    """Гонка двух одинаковых сообщений: второе упирается в уникальность."""
    setup = Setup(save_error=DuplicateVacancyError("already there"))

    await setup.service.process(MESSAGE)

    assert setup.matching.requested == []
    assert setup.observability.skipped == [SkipReason.DUPLICATE]


async def test_unavailable_model_is_not_a_parse_failure() -> None:
    setup = Setup(extractor=FakeExtractor(error=LLMUnavailableError("down")))

    await setup.service.process(MESSAGE)

    assert setup.vacancies.saved == []
    assert setup.observability.skipped == []


async def test_unexpected_failure_reaches_the_caller() -> None:
    """Сбой гасит и считает обработчик скрапера, а не сервис."""
    setup = Setup(extractor=FakeExtractor(error=RuntimeError("boom")))

    with pytest.raises(RuntimeError):
        await setup.service.process(MESSAGE)
