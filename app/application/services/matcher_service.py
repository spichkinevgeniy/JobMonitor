from time import perf_counter

import logfire

from app.application.ports.notification_port import INotificationService
from app.application.ports.observability_port import IObservabilityService
from app.application.ports.unit_of_work import MatchingUnitOfWork
from app.core.logger import get_app_logger
from app.domain.matching.policy import evaluate_match
from app.domain.user.entities import User
from app.domain.user.value_objects import UserId
from app.domain.vacancy.entities import Vacancy
from app.domain.vacancy.value_objects import VacancyId

logger = get_app_logger(__name__)
application_logfire = logfire.with_tags("application")


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
        start = perf_counter()
        with application_logfire.span("matching.match_vacancy", vacancy_id=str(vacancy_id.value)):
            async with self._uow:
                vacancy = await self._uow.vacancies.get_by_id(vacancy_id)
                if vacancy is None:
                    application_logfire.info(
                        "Matching skipped: vacancy not found",
                        vacancy_id=str(vacancy_id.value),
                    )
                    return []

                prefiltered_candidates = await self._load_prefiltered_candidates(vacancy)
                candidate_count = len(prefiltered_candidates)
                logger.debug(
                    "SQL prefilter for %s returned %s candidates",
                    vacancy_id.value,
                    candidate_count,
                )

                matched_user_ids: list[UserId] = []
                rejected_count = 0

                for candidate in prefiltered_candidates:
                    decision = evaluate_match(vacancy=vacancy, user=candidate)
                    if decision.accepted:
                        matched_user_ids.append(candidate.tg_id)
                        self._observe_skill_matches(vacancy=vacancy, user=candidate)
                        continue

                    rejected_count += 1
                    logger.debug(
                        "User %s rejected by %s",
                        candidate.tg_id.value,
                        decision.reason.value if decision.reason else "unknown",
                    )

            await self._notification_service.dispatch_vacancy(
                vacancy_id=vacancy_id.value,
                mirror_chat_id=vacancy.mirror_chat_id,
                mirror_message_id=vacancy.mirror_message_id,
                user_ids=[user_id.value for user_id in matched_user_ids],
            )

            latency_ms = int((perf_counter() - start) * 1000)
            final_count = len(matched_user_ids)
            application_logfire.info(
                "Matching finished",
                vacancy_id=str(vacancy_id.value),
                matched_count=final_count,
                candidate_count=candidate_count,
                latency_ms=latency_ms,
            )
            if candidate_count > 0:
                rejection_ratio = rejected_count / candidate_count
                if rejection_ratio > 0.8:
                    logger.warning(
                        "High rejection ratio for %s after domain checks: %.2f",
                        vacancy_id.value,
                        rejection_ratio,
                    )

            return matched_user_ids

    async def _load_prefiltered_candidates(self, vacancy: Vacancy) -> list[User]:
        specializations = {item.value for item in vacancy.specializations.items}
        skills = {item.value for item in vacancy.skills.items}
        return await self._uow.users.find_prefiltered_candidates(
            specializations=specializations,
            skills=skills,
            is_active=True,
        )

    def _observe_skill_matches(self, vacancy: Vacancy, user: User) -> None:
        vacancy_skills = {skill.value.lower() for skill in vacancy.skills.items}
        user_skills = {skill.value.lower() for skill in user.cv_skills.items}
        for skill in sorted(vacancy_skills & user_skills):
            self._observability.observe_skill_match(skill=skill, count=1)
