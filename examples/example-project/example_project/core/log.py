import logging

from example_project.utils import Env


def set_logger(env: Env):
    logger = logging.getLogger("uvicorn.error" if env != Env.PROD else "gunicorn.error")
    logger.setLevel(logging.INFO)
    return logger

