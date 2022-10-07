from logging.config import dictConfig

from celery import Celery
from celery.signals import setup_logging
from django.conf import settings

app = Celery("builder")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.task_default_queue = "builder"


@setup_logging.connect
def config_loggers(*args, **kwargs):
    dictConfig(settings.CELERY_LOGGING)
