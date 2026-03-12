import logging

from app.core.config import config

ROOT_LOGGER_NAME = "job_monitor"
DEFAULT_LOG_LEVEL = logging.INFO


def _resolve_log_level(raw_level: str) -> int:
    level = logging.getLevelNamesMapping().get(raw_level.upper())
    return level if isinstance(level, int) else DEFAULT_LOG_LEVEL


def setup_root_logger():
    logger = logging.getLogger(ROOT_LOGGER_NAME)
    logger.setLevel(_resolve_log_level(config.LOG_LEVEL))
    logger.propagate = False

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(module)s.%(funcName)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


setup_root_logger()


def get_app_logger(module_name: str):
    return logging.getLogger(f"{ROOT_LOGGER_NAME}.{module_name}")
