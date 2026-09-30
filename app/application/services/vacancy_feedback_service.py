"""Кнопки под присланной вакансией: «Почему прислали?» и «Не подходит»."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from app.application.ports.unit_of_work import MatchingUnitOfWork
from app.domain.matching.entities import MatchRejectionReason
from app.domain.matching.policy import unchecked_filters
from app.domain.user.value_objects import UserId
from app.domain.vacancy.value_objects import VacancyId


@dataclass(frozen=True, slots=True)
class VacancyExplanation:
    """Что совпало с профилем и какие фильтры вакансию не проверили."""

    matched_specializations: list[str]
    matched_skills: list[str]
    unchecked_filters: list[MatchRejectionReason]
    user_work_format: str | None


@dataclass(frozen=True, slots=True)
class VacancySource:
    """Канал и ссылка на исходный пост — для кнопки «Источник»."""

    channel: str | None = None
    url: str | None = None


class VacancyFeedbackService:
    def __init__(self, uow_factory: Callable[[], MatchingUnitOfWork]) -> None:
        self._uow = uow_factory

    async def explain(self, vacancy_id: UUID, user_tg_id: int) -> VacancyExplanation | None:
        """None — эту вакансию человеку не присылали."""
        uow = self._uow()
        async with uow:
            match = await uow.vacancies.get_dispatch_match(VacancyId(vacancy_id), user_tg_id)
            if match is None:
                return None
            vacancy = await uow.vacancies.get_by_id(VacancyId(vacancy_id))
            user = await uow.users.get_by_tg_id(UserId(user_tg_id))

        if vacancy is None or user is None:
            return None
        return VacancyExplanation(
            matched_specializations=match.matched_specializations,
            matched_skills=match.matched_skills,
            unchecked_filters=unchecked_filters(vacancy, user),
            user_work_format=user.cv_work_format.value if user.cv_work_format else None,
        )

    async def reject(self, vacancy_id: UUID, user_tg_id: int) -> None:
        uow = self._uow()
        async with uow:
            await uow.vacancies.reject_dispatch(
                VacancyId(vacancy_id), user_tg_id, datetime.now(UTC)
            )

    async def undo_rejection(self, vacancy_id: UUID, user_tg_id: int) -> None:
        uow = self._uow()
        async with uow:
            await uow.vacancies.clear_dispatch_feedback(VacancyId(vacancy_id), user_tg_id)

    async def source_of(self, vacancy_id: UUID) -> VacancySource:
        """Кнопку источника надо вернуть на место при пересборке клавиатуры.

        Ссылку строит сама вакансия, как и при рассылке. Раньше обработчик
        кнопки собирал её заново и терял тему: у постов из форумов ссылка
        переставала открываться, как только человек отмечал вакансию.
        """
        uow = self._uow()
        async with uow:
            vacancy = await uow.vacancies.get_by_id(VacancyId(vacancy_id))

        if vacancy is None:
            return VacancySource()
        return VacancySource(channel=vacancy.source_channel, url=vacancy.source_url)
