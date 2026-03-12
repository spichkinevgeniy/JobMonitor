import sentry_sdk

from app.bootstrap.bootstrap import build_runtime_components, init_infrastructure
from app.bootstrap.supervisor import run_supervised
from app.core.logger import get_app_logger

logger = get_app_logger(__name__)


async def run_application() -> None:
    try:
        init_infrastructure()
        components = await build_runtime_components()
        await run_supervised(components)
    except Exception as exc:
        logger.exception("Application startup/runtime failed")
        sentry_sdk.capture_exception(exc)
        sentry_sdk.flush()
        raise
