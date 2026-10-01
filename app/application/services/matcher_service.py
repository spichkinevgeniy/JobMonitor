from dataclasses import dataclass
from time import perf_counter

import logfire

from app.application.ports.notification_port import DispatchTarget, INotificationService
from app.application.ports.observability_port import IObservabilityService
from app.application.ports.unit_of_work import MatchingUnitOfWork
from app.core.logger import get_app_logger
from app.core.privacy import user_ref
from app.domain.matching.entities import MatchRejectionReason
from app.domain.matching.policy import evaluate_match
from app.domain.user.entities import User
from app.domain.user.value_objects import UserId
from app.domain.vacancy.entities import Vacancy
from app.domain.vacancy.value_objects import VacancyId

logger = get_app_logger(__name__)
application_logfire = logfire.with_tags("application")


@dataclass(frozen=True, slots=True)
class MatchOutcome:
    """Решение по вакансии: кому отправить и почему отсеяли остальных."""

    accepted: list[User]
    rejected: list[tuple[User, MatchRejectionReason | None]]

    @property
    def candidate_count(self) -> int:
        return len(self.accepted) + len(self.rejected)


def decide_recipients(vacancy: Vacancy, candidates: list[User]) -> MatchOutcome:
    """Кому из кандидатов отправить вакансию.

    Без базы, метрик и рассылки — поэтому решение проверяется обычным тестом.
    """
    accepted: list[User] = []
    rejected: list[tuple[User, MatchRejectionReason | None]] = []
    for candidate in candidates:
        decision = evaluate_match(vacancy=vacancy, user=candidate)
        if decision.accepted:
            accepted.append(candidate)
        else:
            rejected.append((candidate, decision.reason))
    return MatchOutcome(accepted=accepted, rejected=rejected)


def dispatch_target(vacancy: Vacancy, user: User) -> DispatchTarget:
    """Получатель со снимком совпадения: по нему потом отвечают «почему прислали»."""
    return DispatchTarget(
        user_id=user.tg_id.value,
        matched_skills=sorted(item.value for item in vacancy.skills.items & user.cv_skills.items),
        matched_specializations=sorted(
            item.value for item in vacancy.specializations.items & user.cv_specializations.items
        ),
    )


class MatcherService:
    def __init__(
        self,
        uow: MatchingUnitOfWork,
        notification_service: INotificationService,
        observability: IObservabilityService,
    ) -> None:
        self._uow = uow
        self._notification_service = notification_service
        self._observability = observability

    async def match_vacancy(self, vacancy_id: VacancyId) -> list[UserId]:
        """Загрузить кандидатов → решить, кому подходит → разослать."""
        start = perf_counter()
        with application_logfire.span("matching.match_vacancy", vacancy_id=str(vacancy_id.value)):
            loaded = await self._load(vacancy_id)
            if loaded is None:
                application_logfire.info(
                    "Matching skipped: vacancy not found",
                    vacancy_id=str(vacancy_id.value),
                )
                return []
            vacancy, candidates = loaded

            outcome = decide_recipients(vacancy, candidates)
            self._observe(vacancy, outcome)

            await self._notification_service.dispatch_vacancy(
                vacancy_id=vacancy_id.value,
                mirror_chat_id=vacancy.mirror_chat_id,
                mirror_message_id=vacancy.mirror_message_id,
                targets=[dispatch_target(vacancy, user) for user in outcome.accepted],
                source_channel=vacancy.source_channel,
                source_url=vacancy.source_url,
            )

            self._log_finished(vacancy_id, outcome, start)
            return [user.tg_id for user in outcome.accepted]

    async def _load(self, vacancy_id: VacancyId) -> tuple[Vacancy, list[User]] | None:
        """Вакансия и кандидаты, прошедшие SQL-префильтр по специализациям и навыкам."""
        async with self._uow:
            vacancy = await self._uow.vacancies.get_by_id(vacancy_id)
            if vacancy is None:
                return None
            candidates = await self._load_prefiltered_candidates(vacancy)

        logger.debug(
            "SQL prefilter for %s returned %s candidates",
            vacancy_id.value,
            len(candidates),
        )
        return vacancy, candidates

    async def _load_prefiltered_candidates(self, vacancy: Vacancy) -> list[User]:
        specializations = {item.value for item in vacancy.specializations.items}
        skills = {item.value for item in vacancy.skills.items}
        return await self._uow.users.find_prefiltered_candidates(
            specializations=specializations,
            skills=skills,
            is_active=True,
        )

    def _observe(self, vacancy: Vacancy, outcome: MatchOutcome) -> None:
        """Метрики решения: какие навыки совпадают и какие фильтры отсекают."""
        for user in outcome.accepted:
            self._observe_skill_matches(vacancy=vacancy, user=user)
        for user, reason in outcome.rejected:
            if reason is not None:
                self._observability.observe_match_rejected(reason.value)
            logger.debug(
                "User %s rejected by %s",
                user_ref(user.tg_id.value),
                reason.value if reason else "unknown",
            )

    def _log_finished(self, vacancy_id: VacancyId, outcome: MatchOutcome, start: float) -> None:
        application_logfire.info(
            "Matching finished",
            vacancy_id=str(vacancy_id.value),
            matched_count=len(outcome.accepted),
            candidate_count=outcome.candidate_count,
            latency_ms=int((perf_counter() - start) * 1000),
        )
        if outcome.candidate_count > 0:
            rejection_ratio = len(outcome.rejected) / outcome.candidate_count
            if rejection_ratio > 0.8:
                logger.warning(
                    "High rejection ratio for %s after domain checks: %.2f",
                    vacancy_id.value,
                    rejection_ratio,
                )

    def _observe_skill_matches(self, vacancy: Vacancy, user: User) -> None:
        vacancy_skills = {skill.value.lower() for skill in vacancy.skills.items}
        user_skills = {skill.value.lower() for skill in user.cv_skills.items}
        for skill in sorted(vacancy_skills & user_skills):
            self._observability.observe_skill_match(skill=skill, count=1)
