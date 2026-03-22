from app.application.ports.observability_port import IObservabilityService
from app.infrastructure.observability.metrics import (
    ACTIVE_USERS_TOTAL,
    MESSAGES_NOT_VACANCY_TOTAL,
    SKILL_MATCHES_TOTAL,
    USERS_REGISTERED_TOTAL,
    USERS_TOTAL,
    VACANCIES_COLLECTED_TOTAL,
)


class PrometheusObservabilityService(IObservabilityService):
    def observe_vacancy_collected(self, count: int = 1) -> None:
        VACANCIES_COLLECTED_TOTAL.inc(count)

    def observe_not_vacancy_detected(self, count: int = 1) -> None:
        MESSAGES_NOT_VACANCY_TOTAL.inc(count)

    def observe_skill_match(self, skill: str, count: int = 1) -> None:
        SKILL_MATCHES_TOTAL.labels(skill=skill).inc(count)

    def observe_users_registered(self, count: int = 1) -> None:
        USERS_REGISTERED_TOTAL.inc(count)

    def observe_users_snapshot(self, total_users: int, active_users: int) -> None:
        USERS_TOTAL.set(total_users)
        ACTIVE_USERS_TOTAL.set(active_users)


class NoOpObservabilityService(IObservabilityService):
    def observe_vacancy_collected(self, count: int = 1) -> None:
        return None

    def observe_not_vacancy_detected(self, count: int = 1) -> None:
        return None

    def observe_skill_match(self, skill: str, count: int = 1) -> None:
        return None

    def observe_users_registered(self, count: int = 1) -> None:
        return None

    def observe_users_snapshot(self, total_users: int, active_users: int) -> None:
        return None
