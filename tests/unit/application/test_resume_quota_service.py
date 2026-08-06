"""Кулдаун и дневная квота на загрузку резюме."""

from datetime import UTC, datetime, timedelta
from types import TracebackType

import pytest

from app.application.services.resume_quota_service import (
    COOLDOWN,
    DAILY_QUOTA,
    QUOTA_WINDOW,
    QuotaRejection,
    ResumeQuotaService,
)

TG_ID = 777


def _as_utc(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


class FakeUserRepository:
    def __init__(self, uploads: list[datetime]) -> None:
        self.uploads = uploads

    async def get_resume_upload_stats(
        self, tg_id: int, since: datetime
    ) -> tuple[int, datetime | None]:
        # Сравнение по окну в проде делает Postgres. Наружу отдаём как есть.
        mine = [item for item in self.uploads if _as_utc(item) >= since]
        return len(mine), max(self.uploads, key=_as_utc) if self.uploads else None

    async def log_resume_upload(self, tg_id: int) -> None:
        self.uploads.append(datetime.now(UTC))


class FakeUnitOfWork:
    def __init__(self, uploads: list[datetime] | None = None) -> None:
        self.users = FakeUserRepository(uploads or [])
        self.committed = False

    async def __aenter__(self) -> "FakeUnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        return None

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        return None


def _service(uploads: list[datetime] | None = None) -> tuple[ResumeQuotaService, FakeUnitOfWork]:
    uow = FakeUnitOfWork(uploads)
    return ResumeQuotaService(uow), uow  # type: ignore[arg-type]


class TestCooldown:
    async def test_first_upload_is_allowed(self) -> None:
        service, _ = _service()

        assert (await service.check(TG_ID)).allowed

    async def test_upload_right_after_previous_is_rejected(self) -> None:
        service, _ = _service([datetime.now(UTC) - timedelta(seconds=5)])

        decision = await service.check(TG_ID)

        assert not decision.allowed
        assert decision.rejection is QuotaRejection.COOLDOWN
        assert 0 < decision.retry_after_seconds <= COOLDOWN.total_seconds()

    async def test_upload_after_cooldown_is_allowed(self) -> None:
        service, _ = _service([datetime.now(UTC) - COOLDOWN - timedelta(seconds=1)])

        assert (await service.check(TG_ID)).allowed

    async def test_retry_after_never_reports_zero(self) -> None:
        service, _ = _service([datetime.now(UTC) - COOLDOWN + timedelta(milliseconds=1)])

        decision = await service.check(TG_ID)

        assert decision.retry_after_seconds >= 1

    async def test_naive_timestamp_from_db_is_handled(self) -> None:
        service, _ = _service([datetime.now(UTC).replace(tzinfo=None)])

        decision = await service.check(TG_ID)

        assert decision.rejection is QuotaRejection.COOLDOWN


class TestDailyQuota:
    async def test_quota_reached_is_rejected(self) -> None:
        now = datetime.now(UTC)
        uploads = [now - COOLDOWN - timedelta(minutes=index) for index in range(DAILY_QUOTA)]
        service, _ = _service(uploads)

        decision = await service.check(TG_ID)

        assert not decision.allowed
        assert decision.rejection is QuotaRejection.DAILY_QUOTA

    async def test_one_below_quota_is_allowed(self) -> None:
        now = datetime.now(UTC)
        uploads = [now - COOLDOWN - timedelta(minutes=index) for index in range(DAILY_QUOTA - 1)]
        service, _ = _service(uploads)

        assert (await service.check(TG_ID)).allowed

    async def test_uploads_outside_window_do_not_count(self) -> None:
        now = datetime.now(UTC)
        uploads = [now - QUOTA_WINDOW - timedelta(minutes=index) for index in range(DAILY_QUOTA)]
        service, _ = _service(uploads)

        assert (await service.check(TG_ID)).allowed

    async def test_cooldown_wins_over_quota(self) -> None:
        now = datetime.now(UTC)
        uploads = [now - timedelta(seconds=index) for index in range(DAILY_QUOTA)]
        service, _ = _service(uploads)

        assert (await service.check(TG_ID)).rejection is QuotaRejection.COOLDOWN


class TestRegister:
    async def test_register_writes_and_commits(self) -> None:
        service, uow = _service()

        await service.register(TG_ID)

        assert len(uow.users.uploads) == 1
        assert uow.committed

    async def test_registered_upload_blocks_the_next_one(self) -> None:
        service, _ = _service()

        await service.register(TG_ID)

        assert not (await service.check(TG_ID)).allowed


@pytest.mark.parametrize("count", [0, 1, DAILY_QUOTA - 1, DAILY_QUOTA, DAILY_QUOTA + 5])
async def test_decision_is_consistent_for_any_history(count: int) -> None:
    now = datetime.now(UTC)
    uploads = [now - COOLDOWN - timedelta(minutes=index) for index in range(count)]
    service, _ = _service(uploads)

    decision = await service.check(TG_ID)

    assert decision.allowed is (count < DAILY_QUOTA)
    assert decision.allowed or decision.retry_after_seconds >= 1
