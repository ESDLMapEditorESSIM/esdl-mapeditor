import logging

import settings


def get_logger(name):
    logger = logging.getLogger(name)
    logger.propagate = False

    if settings.FLASK_DEBUG:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(levelname).3s/%(asctime)s/%(name)s - %(message)s")
    )
    logger.addHandler(handler)

    return logger
