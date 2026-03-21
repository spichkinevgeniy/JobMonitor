import logging

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.pydantic_ai import PydanticAIIntegration

from app.core.config import config


def init_sentry() -> None:
    if not config.SENTRY_DSN:
        return

    logging_integration = LoggingIntegration(
        level=logging.INFO,
        event_level=logging.ERROR,
    )

    sentry_sdk.init(
        dsn=config.SENTRY_DSN,
        environment=config.SENTRY_ENV,
        traces_sample_rate=config.SENTRY_TRACES_SAMPLE_RATE,
        integrations=[logging_integration, FastApiIntegration()],
        disabled_integrations=[PydanticAIIntegration()],
    )
