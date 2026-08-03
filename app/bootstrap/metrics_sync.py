import asyncio

from app.application.services.user_service import UserService
from app.core.logger import get_app_logger

logger = get_app_logger(__name__)

METRICS_SYNC_INTERVAL_SECONDS = 300


async def run_metrics_sync_loop(user_service: UserService) -> None:
    while True:
        await asyncio.sleep(METRICS_SYNC_INTERVAL_SECONDS)
        try:
            await user_service.sync_user_metrics()
        except Exception:
            logger.exception("Failed to sync user metrics")
