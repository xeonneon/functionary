"""Celery Worker App

Instantiates a Celery App that will connect to a Redis instance
to retrieve its internal queue of work to perform.

"""

import os
from logging.config import dictConfig

from celery import Celery
from celery.signals import setup_logging

BROKER_WORKDIR = os.getenv("BROKER_WORKDIR", "/tmp")
BROKER_WORKDIR_PATH = os.path.join(BROKER_WORKDIR, "broker")

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
    include=["runner.handlers"],
)

app.conf.update(
    {
        "broker_url": "filesystem://",
        "broker_transport_options": {
            "data_folder_in": BROKER_WORKDIR_PATH,
            "data_folder_out": BROKER_WORKDIR_PATH,
        },
        "result_persistent": False,
        "task_serializer": "json",
        "result_serializer": "json",
        "accept_content": ["json"],
    }
)


@setup_logging.connect
def config_loggers(*args, **kwargs):
    dictConfig(LOGGING)


if __name__ == "__main__":
    app.start()
