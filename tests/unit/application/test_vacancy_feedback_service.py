"""Кнопки под вакансией: объяснение, отметка «не подходит» и ссылка на источник."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from app.application.services.vacancy_feedback_service import (
    VacancyExplanation,
    VacancyFeedbackService,
    VacancySource,
)
from app.domain.matching.entities import MatchRejectionReason
from app.domain.shared import WorkFormat
from app.domain.user.entities import User
from app.domain.user.value_objects import FilterMode, UserId
from app.domain.vacancy.entities import DispatchMatch, Vacancy
from app.domain.vacancy.value_objects import VacancyId

USER_ID = 42


def _vacancy(**kwargs: Any) -> Vacancy:
    fields: dict[str, Any] = {
        "work_format": WorkFormat.UNDEFINED,
        "source_channel": "@front_end_jobs",
        "source_message_id": 16740,
    }
    return Vacancy.create(
        vacancy_id=uuid4(),
        text="Frontend-разработчик на React",
        specializations_raw=["Frontend"],
        skills_raw=["React", "TypeScript"],
        mirror_chat_id=-100,
        mirror_message_id=7,
        **{**fields, **kwargs},
    )


class FakeVacancies:
    def __init__(self, vacancy: Vacancy | None, match: DispatchMatch | None) -> None:
        self._vacancy = vacancy
        self._match = match
        self.feedback: list[tuple[str, UUID, int]] = []

    async def get_by_id(self, vacancy_id: VacancyId) -> Vacancy | None:
        return self._vacancy

    async def get_dispatch_match(
        self, vacancy_id: VacancyId, user_tg_id: int
    ) -> DispatchMatch | None:
        return self._match if user_tg_id == USER_ID else None

    async def reject_dispatch(self, vacancy_id: VacancyId, user_tg_id: int, at: datetime) -> None:
        self.feedback.append(("rejected", vacancy_id.value, user_tg_id))

    async def clear_dispatch_feedback(self, vacancy_id: VacancyId, user_tg_id: int) -> None:
        self.feedback.append(("cleared", vacancy_id.value, user_tg_id))


class FakeUsers:
    def __init__(self, user: User | None) -> None:
        self._user = user

    async def get_by_tg_id(self, tg_id: UserId) -> User | None:
        return self._user if self._user and self._user.tg_id == tg_id else None


class FakeUow:
    def __init__(self, vacancies: FakeVacancies, users: FakeUsers) -> None:
        self.vacancies = vacancies
        self.users = users

    async def __aenter__(self) -> "FakeUow":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


def _service(
    vacancy: Vacancy | None,
    match: DispatchMatch | None = None,
    user: User | None = None,
) -> tuple[VacancyFeedbackService, FakeVacancies]:
    vacancies = FakeVacancies(vacancy, match)
    uow = FakeUow(vacancies, FakeUsers(user))
    return VacancyFeedbackService(lambda: uow), vacancies  # type: ignore[arg-type, return-value]


def _strict_remote_user() -> User:
    return User.create(
        tg_id=USER_ID,
        cv_specializations_raw=["Frontend"],
        cv_skills_raw=["React"],
        cv_work_format=WorkFormat.REMOTE,
        filter_work_format_mode=FilterMode.STRICT,
    )


async def test_explains_what_matched_and_which_filter_let_it_through() -> None:
    vacancy = _vacancy()
    service, _ = _service(
        vacancy,
        DispatchMatch(matched_specializations=["Frontend"], matched_skills=["React"]),
        _strict_remote_user(),
    )

    explanation = await service.explain(vacancy.id.value, USER_ID)

    assert explanation == VacancyExplanation(
        matched_specializations=["Frontend"],
        matched_skills=["React"],
        unchecked_filters=[MatchRejectionReason.FORMAT],
        user_work_format="REMOTE",
    )


async def test_nothing_to_explain_if_vacancy_was_not_sent_to_this_user() -> None:
    vacancy = _vacancy()
    service, _ = _service(vacancy, match=None, user=_strict_remote_user())

    assert await service.explain(vacancy.id.value, USER_ID) is None


async def test_reject_and_undo_touch_only_this_users_dispatch() -> None:
    vacancy = _vacancy()
    service, vacancies = _service(vacancy)

    await service.reject(vacancy.id.value, USER_ID)
    await service.undo_rejection(vacancy.id.value, USER_ID)

    assert vacancies.feedback == [
        ("rejected", vacancy.id.value, USER_ID),
        ("cleared", vacancy.id.value, USER_ID),
    ]


async def test_forum_source_link_keeps_its_topic() -> None:
    """Раньше после «Не подходит» ссылка теряла тему и переставала открываться."""
    vacancy = _vacancy(source_topic_id=2)
    service, _ = _service(vacancy)

    source = await service.source_of(vacancy.id.value)

    assert source == VacancySource(
        channel="@front_end_jobs",
        url="https://t.me/front_end_jobs/2/16740",
    )


async def test_source_is_the_same_as_in_the_original_message() -> None:
    """Кнопку пересобирают после отметки — она должна остаться прежней."""
    vacancy = _vacancy()
    service, _ = _service(vacancy)

    source = await service.source_of(vacancy.id.value)

    assert (source.channel, source.url) == (vacancy.source_channel, vacancy.source_url)


async def test_no_source_for_missing_vacancy() -> None:
    service, _ = _service(None)

    assert await service.source_of(uuid4()) == VacancySource()
