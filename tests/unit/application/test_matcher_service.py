from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from app.application.ports.notification_port import DispatchTarget
from app.application.services.matcher_service import (
    MatcherService,
    decide_recipients,
    dispatch_target,
)
from app.domain.matching.entities import MatchRejectionReason
from app.domain.shared import WorkFormat
from app.domain.user.entities import User
from app.domain.user.value_objects import FilterMode, UserId
from app.domain.vacancy.entities import Vacancy
from app.domain.vacancy.value_objects import VacancyId


@dataclass
class _ObservabilitySpy:
    seen: list[tuple[str, int]]

    def observe_skill_match(self, skill: str, count: int = 1) -> None:
        self.seen.append((skill, count))


class _NotificationDummy:
    async def dispatch_vacancy(self, **_: object) -> None:
        return None


class _UnitOfWorkDummy:
    pass


def test_observe_skill_matches_tracks_shared_skills() -> None:
    observability = _ObservabilitySpy(seen=[])
    service = MatcherService(
        uow=_UnitOfWorkDummy(),  # type: ignore[arg-type]
        notification_service=_NotificationDummy(),  # type: ignore[arg-type]
        observability=observability,  # type: ignore[arg-type]
    )
    vacancy = Vacancy.create(
        vacancy_id=uuid4(),
        text="Frontend engineer with React and Vue",
        specializations_raw=["Frontend"],
        skills_raw=["React", "Vue"],
        mirror_chat_id=1,
        mirror_message_id=1,
        work_format=WorkFormat.REMOTE,
    )
    user = User.create(
        tg_id=1,
        cv_specializations_raw=["Frontend"],
        cv_skills_raw=["Vue", "Python"],
    )

    service._observe_skill_matches(vacancy=vacancy, user=user)

    assert observability.seen == [("vue", 1)]


def _vacancy() -> Vacancy:
    """Бэкенд в офисе за 150 000 ₽."""
    return Vacancy.create(
        vacancy_id=uuid4(),
        text="Backend-разработчик на Python, офис, 150 000 ₽",
        specializations_raw=["Backend"],
        skills_raw=["Python", "SQL"],
        mirror_chat_id=-100,
        mirror_message_id=7,
        work_format=WorkFormat.ONSITE,
        salary_amount=150_000,
        salary_currency="RUB",
    )


def _candidate(tg_id: int, **kwargs: Any) -> User:
    return User.create(
        tg_id=tg_id,
        cv_specializations_raw=["Backend"],
        cv_skills_raw=["Python"],
        **kwargs,
    )


def _wants_more_money(tg_id: int) -> User:
    return _candidate(tg_id, cv_salary_amount=300_000, filter_salary_mode=FilterMode.STRICT)


class TestDecision:
    """Кому отправить — решается без базы, метрик и рассылки."""

    def test_splits_candidates_by_their_filters(self) -> None:
        fits = _candidate(1)
        wants_more_money = _wants_more_money(2)
        remote_only = _candidate(
            3, cv_work_format=WorkFormat.REMOTE, filter_work_format_mode=FilterMode.STRICT
        )

        outcome = decide_recipients(_vacancy(), [fits, wants_more_money, remote_only])

        assert outcome.accepted == [fits]
        assert outcome.rejected == [
            (wants_more_money, MatchRejectionReason.SALARY),
            (remote_only, MatchRejectionReason.FORMAT),
        ]

    def test_target_remembers_what_matched(self) -> None:
        """По этому снимку потом отвечают на «Почему прислали?»."""
        user = User.create(
            tg_id=7,
            cv_specializations_raw=["Frontend", "Backend"],
            cv_skills_raw=["SQL", "Go", "Python"],
        )

        assert dispatch_target(_vacancy(), user) == DispatchTarget(
            user_id=7,
            matched_skills=["Python", "SQL"],
            matched_specializations=["Backend"],
        )


class _Vacancies:
    def __init__(self, vacancy: Vacancy | None) -> None:
        self._vacancy = vacancy

    async def get_by_id(self, vacancy_id: VacancyId) -> Vacancy | None:
        return self._vacancy


class _Users:
    def __init__(self, candidates: list[User]) -> None:
        self._candidates = candidates

    async def find_prefiltered_candidates(self, **_: object) -> list[User]:
        return self._candidates


class _Uow:
    def __init__(self, vacancy: Vacancy | None, candidates: list[User]) -> None:
        self.vacancies = _Vacancies(vacancy)
        self.users = _Users(candidates)

    async def __aenter__(self) -> "_Uow":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


@dataclass
class _Metrics:
    rejected: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)

    def observe_match_rejected(self, reason: str) -> None:
        self.rejected.append(reason)

    def observe_skill_match(self, skill: str, count: int = 1) -> None:
        self.skills.append(skill)


class _Notifications:
    def __init__(self) -> None:
        self.dispatched: list[dict[str, Any]] = []

    async def dispatch_vacancy(self, **kwargs: Any) -> None:
        self.dispatched.append(kwargs)


def _service(uow: _Uow, notifications: _Notifications, metrics: _Metrics) -> MatcherService:
    return MatcherService(
        uow=uow,  # type: ignore[arg-type]
        notification_service=notifications,  # type: ignore[arg-type]
        observability=metrics,  # type: ignore[arg-type]
    )


class TestMatchVacancy:
    async def test_sends_to_those_who_fit_and_counts_the_rest(self) -> None:
        vacancy = _vacancy()
        notifications, metrics = _Notifications(), _Metrics()
        service = _service(
            _Uow(vacancy, [_candidate(1), _wants_more_money(2)]), notifications, metrics
        )

        sent_to = await service.match_vacancy(vacancy.id)

        assert sent_to == [UserId(1)]
        assert [call["targets"] for call in notifications.dispatched] == [
            [
                DispatchTarget(
                    user_id=1, matched_skills=["Python"], matched_specializations=["Backend"]
                )
            ]
        ]
        assert metrics.rejected == ["salary"]
        assert metrics.skills == ["python"]

    async def test_missing_vacancy_sends_nothing(self) -> None:
        notifications = _Notifications()
        service = _service(_Uow(None, []), notifications, _Metrics())

        assert await service.match_vacancy(VacancyId(uuid4())) == []
        assert notifications.dispatched == []
