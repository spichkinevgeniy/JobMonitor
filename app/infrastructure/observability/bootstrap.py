import logfire
from prometheus_client import start_http_server

from app.application.ports.observability_port import IObservabilityService
from app.core.config import config
from app.core.logger import get_app_logger
from app.infrastructure.db.session import engine
from app.infrastructure.observability.service import (
    NoOpObservabilityService,
    PrometheusObservabilityService,
)

logger = get_app_logger(__name__)


def _has_logfire_token() -> bool:
    token = config.LOGFIRE_TOKEN
    return bool(token and token.strip())


def _get_logfire_min_level() -> str:
    level = config.LOG_LEVEL.strip().lower()
    if level == "critical":
        return "fatal"
    return "warning" if level == "warning" else level


def init_logfire() -> None:
    if not config.LOGFIRE_ENABLED:
        logger.info("Logfire disabled by config")
        return

    token_present = _has_logfire_token()
    if config.APP_ENV == "production" and not token_present:
        raise RuntimeError("LOGFIRE_TOKEN must be set when LOGFIRE_ENABLED=true in production.")
    if not token_present:
        logger.warning(
            "LOGFIRE_TOKEN is empty; Logfire telemetry will not be sent to Logfire Cloud."
        )

    try:
        logfire.configure(
            send_to_logfire="if-token-present",
            token=config.LOGFIRE_TOKEN,
            service_name=config.LOGFIRE_SERVICE_NAME,
            environment=config.LOGFIRE_ENV,
            min_level=_get_logfire_min_level(),
            distributed_tracing=True,
        )
        logfire.instrument_pydantic_ai(
            include_content=False,
            include_binary_content=False,
        )
        logfire.instrument_sqlalchemy(engine)
        logfire.instrument_system_metrics()
        logger.info("Logfire initialized")
    except Exception:
        logger.exception("Failed to initialize Logfire; continuing without it")


def init_metrics_server() -> None:
    if not config.METRICS_ENABLED:
        logger.info("Metrics server disabled by config")
        return

    start_http_server(port=config.METRICS_PORT, addr=config.METRICS_ADDR)
    logger.info(
        "Metrics server started at %s:%s",
        config.METRICS_ADDR,
        config.METRICS_PORT,
    )


def build_observability_service() -> IObservabilityService:
    if config.METRICS_ENABLED:
        return PrometheusObservabilityService()
    return NoOpObservabilityService()
