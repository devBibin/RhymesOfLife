import logging
import logging.handlers

import os
BASE_DIR = os.path.dirname(os.path.realpath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)


def create_log(name, source):
    log_filename = os.path.join(LOG_DIR, name)
    error_filename = os.path.join(LOG_DIR, "error.log")
    # Set up a specific logger with our desired output level
    log = logging.Logger(source)
    log.setLevel(logging.DEBUG)

    formatter = logging.Formatter("[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s")

    # Add the log message handler to the logger
    handler = logging.handlers.RotatingFileHandler(
                  log_filename, maxBytes=2000000, backupCount=5, encoding="utf-8")

    handler.setFormatter(formatter)
    log.addHandler(handler)

    error_handler = logging.handlers.RotatingFileHandler(
        error_filename,
        maxBytes=2000000,
        backupCount=5,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    log.addHandler(error_handler)
    return log
