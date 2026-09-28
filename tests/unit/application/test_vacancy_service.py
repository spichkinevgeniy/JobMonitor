"""Разбор сообщения: что идёт дальше, а что пропускается без ошибки."""

from uuid import uuid4

import pytest

from app.application.dto import InfoRawVacancy, OutVacancyParse
from app.application.dto.resume_dto import SkillWithEvidence
from app.application.ports.observability_port import SkipReason
from app.application.services.vacancy_service import VacancyService, nothing_to_match_on
from app.domain.shared import WorkFormat
from app.domain.shared.value_objects import SkillType, SpecializationType
from app.domain.vacancy.entities import Vacancy
from app.domain.vacancy.exceptions import ValidationError

TEXT = "Ищем Python-разработчика в платёжную команду. Удалённо, @hr"
BACKEND = (SpecializationType.BACKEND,)
PYTHON = (SkillType.PYTHON,)


class FakeExtractor:
    def __init__(self, result: OutVacancyParse) -> None:
        self.result = result

    async def parse_vacancy(self, text: str) -> OutVacancyParse:
        return self.result


class ObservabilitySpy:
    def __init__(self) -> None:
        self.skipped: list[SkipReason] = []
        self.not_vacancy = 0

    def observe_message_skipped(self, reason: SkipReason) -> None:
        self.skipped.append(reason)

    def observe_not_vacancy_detected(self, count: int = 1) -> None:
        self.not_vacancy += count


def parsed(
    *,
    is_vacancy: bool = True,
    specializations: tuple[SpecializationType, ...] = BACKEND,
    skills: tuple[SkillType, ...] = PYTHON,
) -> OutVacancyParse:
    return OutVacancyParse(
        is_vacancy=is_vacancy,
        specializations=list(specializations),
        skills=[SkillWithEvidence(skill=skill, evidence=skill.value) for skill in skills],
    )


async def parse(result: OutVacancyParse) -> tuple[OutVacancyParse | None, ObservabilitySpy]:
    spy = ObservabilitySpy()
    service = VacancyService(
        uow=None,  # type: ignore[arg-type]  # разбор в базу не ходит
        extractor=FakeExtractor(result),
        observability=spy,  # type: ignore[arg-type]
    )
    raw = InfoRawVacancy(text=TEXT, chat_id=1, message_id=2)
    return await service.parse_message(raw), spy


class TestParseMessage:
    async def test_vacancy_with_specialization_and_skills_goes_on(self) -> None:
        expected = parsed()

        result, spy = await parse(expected)

        assert result is expected
        assert spy.skipped == []

    async def test_no_specialization_is_a_quiet_skip(self) -> None:
        """Раньше такой исход падал исключением и писался в лог как ошибка."""
        result, spy = await parse(parsed(specializations=()))

        assert result is None
        assert spy.skipped == [SkipReason.NO_SPECIALIZATION]

    async def test_no_skills_is_a_quiet_skip(self) -> None:
        result, spy = await parse(parsed(skills=()))

        assert result is None
        assert spy.skipped == [SkipReason.NO_SKILLS]

    async def test_not_a_vacancy_is_counted_as_such(self) -> None:
        result, spy = await parse(parsed(is_vacancy=False, specializations=(), skills=()))

        assert result is None
        assert spy.skipped == [SkipReason.NOT_VACANCY]
        assert spy.not_vacancy == 1


@pytest.mark.parametrize(
    ("specializations", "skills"),
    [(BACKEND, PYTHON), ((), PYTHON), (BACKEND, ()), ((), ())],
)
def test_check_agrees_with_domain(
    specializations: tuple[SpecializationType, ...], skills: tuple[SkillType, ...]
) -> None:
    """Проверка сервиса и инвариант домена обязаны совпадать.

    Разойдутся — и либо снова полетят исключения, либо годная вакансия
    пропадёт молча.
    """
    try:
        Vacancy.create(
            vacancy_id=uuid4(),
            text=TEXT,
            specializations_raw=[item.value for item in specializations],
            skills_raw=[item.value for item in skills],
            mirror_chat_id=1,
            mirror_message_id=1,
            work_format=WorkFormat.REMOTE,
        )
        domain_accepts = True
    except ValidationError:
        domain_accepts = False

    check = nothing_to_match_on(parsed(specializations=specializations, skills=skills))

    assert (check is None) == domain_accepts
