import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.logger import get_app_logger
from app.infrastructure.observability.counter_store import PersistentCounterStore
from app.infrastructure.observability.db_snapshot import collect_db_snapshot
from app.infrastructure.observability.metrics import (
    ACTIVE_USERS_TOTAL,
    AVG_SKILLS_PER_PROFILE,
    DISPATCHED_BY_SKILL,
    DISPATCHED_BY_SPECIALIZATION,
    FEATURE_USED,
    LLM_COST_MICRO_USD,
    LLM_TOKENS,
    MATCH_REJECTED,
    MESSAGES_SKIPPED,
    USERS_TOTAL,
    USERS_WITH_PROFILE,
    USERS_WITHOUT_DISPATCH,
    VACANCIES_DISPATCHED,
    VACANCY_FEEDBACK,
)
from app.infrastructure.observability.service import (
    COUNTER_FEATURE_USED,
    COUNTER_LLM_COST_MICRO,
    COUNTER_LLM_TOKENS,
    COUNTER_MATCH_REJECTED,
    COUNTER_MESSAGES_SKIPPED,
)

logger = get_app_logger(__name__)

METRICS_SYNC_INTERVAL_SECONDS = 60

_COUNTER_GAUGES = {
    COUNTER_MESSAGES_SKIPPED: (MESSAGES_SKIPPED, "reason"),
    COUNTER_FEATURE_USED: (FEATURE_USED, "feature"),
    COUNTER_MATCH_REJECTED: (MATCH_REJECTED, "reason"),
    COUNTER_LLM_TOKENS: (LLM_TOKENS, "kind"),
    COUNTER_LLM_COST_MICRO: (LLM_COST_MICRO_USD, "model"),
}


async def sync_metrics(
    session_factory: async_sessionmaker[AsyncSession],
    counter_store: PersistentCounterStore,
) -> None:
    """Один цикл: слить накопленное, вычитать истину из БД, разложить по метрикам.

    Значения приходят из базы целиком, а не накапливаются в процессе, —
    поэтому перезапуск их не обнуляет.
    """
    totals = await counter_store.flush()
    for (name, label), value in totals.items():
        target = _COUNTER_GAUGES.get(name)
        if target is None:
            continue
        gauge, label_name = target
        gauge.labels(**{label_name: label}).set(value)

    snapshot = await collect_db_snapshot(session_factory)
    USERS_TOTAL.set(snapshot.users_total)
    ACTIVE_USERS_TOTAL.set(snapshot.users_active)
    USERS_WITH_PROFILE.set(snapshot.users_with_profile)
    USERS_WITHOUT_DISPATCH.set(snapshot.users_without_dispatch)
    AVG_SKILLS_PER_PROFILE.set(snapshot.avg_skills_per_profile)
    VACANCIES_DISPATCHED.set(snapshot.vacancies_dispatched)

    for specialization, count in snapshot.dispatched_by_specialization.items():
        DISPATCHED_BY_SPECIALIZATION.labels(specialization=specialization).set(count)
    for skill, count in snapshot.dispatched_by_skill.items():
        DISPATCHED_BY_SKILL.labels(skill=skill).set(count)
    for verdict, count in snapshot.feedback_by_verdict.items():
        VACANCY_FEEDBACK.labels(verdict=verdict).set(count)


async def run_metrics_sync_loop(
    session_factory: async_sessionmaker[AsyncSession],
    counter_store: PersistentCounterStore,
) -> None:
    while True:
        try:
            await sync_metrics(session_factory, counter_store)
        except Exception:
            logger.exception("Failed to sync metrics")
        await asyncio.sleep(METRICS_SYNC_INTERVAL_SECONDS)
