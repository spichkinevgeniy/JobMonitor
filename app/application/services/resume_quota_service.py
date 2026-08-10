"""Кулдаун и дневная квота на загрузку резюме."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from app.application.ports.unit_of_work import UserUnitOfWork
from app.core.logger import get_app_logger
from app.core.privacy import user_ref

logger = get_app_logger(__name__)

DAILY_QUOTA = 10
COOLDOWN = timedelta(minutes=1)
QUOTA_WINDOW = timedelta(days=1)


class QuotaRejection(StrEnum):
    COOLDOWN = "cooldown"
    DAILY_QUOTA = "daily_quota"


@dataclass(frozen=True, slots=True)
class QuotaDecision:
    allowed: bool
    rejection: QuotaRejection | None = None
    retry_after: timedelta | None = None

    @property
    def retry_after_seconds(self) -> int:
        """Округляем вверх, чтобы не отвечать «подождите 0 секунд»."""
        if self.retry_after is None:
            return 0
        return max(1, -(-int(self.retry_after.total_seconds()) // 1))


class ResumeQuotaService:
    def __init__(self, uow: UserUnitOfWork) -> None:
        self._uow = uow

    async def check(self, tg_id: int) -> QuotaDecision:
        now = datetime.now(UTC)
        async with self._uow:
            uploads_in_window, last_uploaded_at = await self._uow.users.get_resume_upload_stats(
                tg_id, since=now - QUOTA_WINDOW
            )

        if last_uploaded_at is not None:
            elapsed = now - _as_utc(last_uploaded_at)
            if elapsed < COOLDOWN:
                return QuotaDecision(
                    allowed=False,
                    rejection=QuotaRejection.COOLDOWN,
                    retry_after=COOLDOWN - elapsed,
                )

        if uploads_in_window >= DAILY_QUOTA:
            logger.info("Resume rejected: daily quota reached (user=%s)", user_ref(tg_id))
            return QuotaDecision(
                allowed=False,
                rejection=QuotaRejection.DAILY_QUOTA,
                retry_after=QUOTA_WINDOW,
            )

        return QuotaDecision(allowed=True)

    async def register(self, tg_id: int) -> None:
        async with self._uow:
            await self._uow.users.log_resume_upload(tg_id)
            await self._uow.commit()


def _as_utc(value: datetime) -> datetime:
    """Из БД дата может прийти без зоны."""
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
