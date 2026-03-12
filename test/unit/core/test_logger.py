import logging

from app.core.logger import (
    DEFAULT_LOG_LEVEL,
    ROOT_LOGGER_NAME,
    _resolve_log_level,
    setup_root_logger,
)


def test_resolve_log_level_falls_back_to_info_for_unknown_value() -> None:
    assert _resolve_log_level("not-a-level") == DEFAULT_LOG_LEVEL


def test_setup_root_logger_is_idempotent() -> None:
    logger = logging.getLogger(ROOT_LOGGER_NAME)
    original_handlers = list(logger.handlers)
    original_level = logger.level
    original_propagate = logger.propagate

    try:
        logger.handlers.clear()

        first = setup_root_logger()
        second = setup_root_logger()

        assert first is second
        assert len(first.handlers) == 1
        assert first.propagate is False
    finally:
        logger.handlers.clear()
        logger.handlers.extend(original_handlers)
        logger.setLevel(original_level)
        logger.propagate = original_propagate
