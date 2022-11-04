# Without this implementation of __init__.py, Celery-Beat is unable to
# view the registered Celery tasks that live inside the core module.

from .celery import app as celery_app

__all__ = ("celery_app",)
