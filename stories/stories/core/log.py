
import logging

from stories.utils.env import Env


def set_logger(env: Env):
    logger = logging.getLogger("uvicorn.error" if env != Env.PROD else "gunicorn.error")
    logger.setLevel(logging.INFO)
    return logger

