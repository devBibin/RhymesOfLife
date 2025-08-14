import logging
import logging.handlers

import os
BASE_DIR = os.path.dirname(os.path.realpath(__file__))


def create_log(name, source):
    LOG_FILENAME = BASE_DIR + "/logs/" + name
    # Set up a specific logger with our desired output level
    log = logging.Logger(source)
    log.setLevel(logging.DEBUG)

    formatter = logging.Formatter("[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s")

    # Add the log message handler to the logger
    handler = logging.handlers.RotatingFileHandler(
                  LOG_FILENAME, maxBytes=2000000, backupCount=5)

    handler.setFormatter(formatter)
    log.addHandler(handler)
    return log
