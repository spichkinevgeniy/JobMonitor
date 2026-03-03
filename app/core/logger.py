import logging


def setup_root_logger():
    root_name = "job_monitor"
    logger = logging.getLogger(root_name)
    logger.setLevel(logging.DEBUG)

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
    return logging.getLogger(f"job_monitor.{module_name}")
