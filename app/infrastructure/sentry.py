import logging

import sentry_sdk
from sentry_sdk.integrations import Integration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from app.core.config import config

# Импорт падает, когда рядом нет дистрибутива pydantic-ai: с переходом на
# pydantic-ai-slim интеграция недоступна и включиться не может, так что
# отключать становится нечего. Ловим, чтобы не ронять приложение на старте.
try:
    from sentry_sdk.integrations.pydantic_ai import PydanticAIIntegration
except Exception:  # noqa: BLE001 — sentry поднимает своё DidNotEnable
    _disabled_integrations: list[Integration] = []
else:
    _disabled_integrations = [PydanticAIIntegration()]


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
        disabled_integrations=_disabled_integrations,
    )
