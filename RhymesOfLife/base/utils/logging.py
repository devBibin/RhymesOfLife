import logging
import logging.handlers
import os
from django.conf import settings

LOG_DIR = getattr(settings, "LOG_DIR", os.path.join(settings.BASE_DIR, "logs"))
os.makedirs(LOG_DIR, exist_ok=True)


def _build_handler(filename: str, *, level: int | None = None) -> logging.Handler:
    handler = logging.handlers.RotatingFileHandler(
        os.path.join(LOG_DIR, filename),
        maxBytes=2_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s"
    )
    handler.setFormatter(fmt)
    if level is not None:
        handler.setLevel(level)
    return handler


def get_app_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
        logger.addHandler(_build_handler("app.log"))
        logger.addHandler(_build_handler("error.log", level=logging.ERROR))
        if settings.DEBUG:
            console = logging.StreamHandler()
            console.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
            logger.addHandler(console)
        logger.propagate = False
    return logger


def get_security_logger() -> logging.Logger:
    logger = logging.getLogger("security")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        logger.addHandler(_build_handler("security.log"))
        logger.addHandler(_build_handler("error.log", level=logging.ERROR))
        logger.propagate = False
    return logger


def get_uploads_logger() -> logging.Logger:
    logger = logging.getLogger("uploads")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        logger.addHandler(_build_handler("uploads.log"))
        logger.addHandler(_build_handler("error.log", level=logging.ERROR))
        logger.propagate = False
    return logger
