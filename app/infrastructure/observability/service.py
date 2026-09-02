from app.application.ports.observability_port import (
    Feature,
    IObservabilityService,
    SkipReason,
    TokenKind,
)
from app.infrastructure.observability.counter_store import PersistentCounterStore
from app.infrastructure.observability.metrics import (
    ACTIVE_USERS_TOTAL,
    MESSAGES_NOT_VACANCY_TOTAL,
    SKILL_MATCHES_TOTAL,
    USERS_REGISTERED_TOTAL,
    USERS_TOTAL,
    VACANCIES_COLLECTED_TOTAL,
)

# Имена в БД: под ними счётчики лежат в metric_counter и переживают
# перезапуск. Меняя их, потеряешь накопленное.
COUNTER_MESSAGES_SKIPPED = "messages_skipped"
COUNTER_FEATURE_USED = "feature_used"
COUNTER_MATCH_REJECTED = "match_rejected"
COUNTER_LLM_TOKENS = "llm_tokens"
COUNTER_LLM_COST_MICRO = "llm_cost_micro"


class PrometheusObservabilityService(IObservabilityService):
    def __init__(self, counter_store: PersistentCounterStore | None = None) -> None:
        self._counters = counter_store

    def observe_message_skipped(self, reason: SkipReason, count: int = 1) -> None:
        if self._counters is not None:
            self._counters.increment(COUNTER_MESSAGES_SKIPPED, reason.value, count)

    def observe_feature_used(self, feature: Feature, count: int = 1) -> None:
        if self._counters is not None:
            self._counters.increment(COUNTER_FEATURE_USED, feature.value, count)

    def observe_match_rejected(self, reason: str, count: int = 1) -> None:
        if self._counters is not None:
            self._counters.increment(COUNTER_MATCH_REJECTED, reason, count)

    def observe_llm_tokens(self, kind: TokenKind, tokens: int) -> None:
        if self._counters is not None and tokens > 0:
            self._counters.increment(COUNTER_LLM_TOKENS, kind.value, tokens)

    def observe_llm_cost(self, model: str, micro_usd: int) -> None:
        if self._counters is not None and micro_usd > 0:
            self._counters.increment(COUNTER_LLM_COST_MICRO, model, micro_usd)

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
    def observe_message_skipped(self, reason: SkipReason, count: int = 1) -> None:
        return None

    def observe_feature_used(self, feature: Feature, count: int = 1) -> None:
        return None

    def observe_match_rejected(self, reason: str, count: int = 1) -> None:
        return None

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

    def observe_llm_tokens(self, kind: TokenKind, tokens: int) -> None:
        return None

    def observe_llm_cost(self, model: str, micro_usd: int) -> None:
        return None
