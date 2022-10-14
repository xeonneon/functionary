"""Celery Worker App

Instantiates a Celery App that will connect to a Redis instance
to retrieve its internal queue of work to perform.

"""

import os
from logging.config import dictConfig

from celery import Celery
from celery.signals import setup_logging

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "[{levelname:<8}] {asctime:<24} {message}", "style": "{"},
    },
    "handlers": {
        "console": {
            "level": os.getenv("LOG_LEVEL", "INFO").upper(),
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "celery": {
            "handlers": ["console"],
            "propagate": False,
        },
        "kombu": {
            "handlers": ["console"],
            "propagate": False,
        },
    },
}

app = Celery(
    "runner",
    broker=f"redis://{REDIS_HOST}:{REDIS_PORT}",
    include=["runner.handlers"],
)


@setup_logging.connect
def config_loggers(*args, **kwargs):
    dictConfig(LOGGING)


if __name__ == "__main__":
    app.start()
