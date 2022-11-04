from os import getenv

from celery.apps.beat import Beat
from django.core.management.base import BaseCommand
from django_celery_beat import schedulers

from core.celery import app
from core.utils.messaging import initialize_messaging, wait_for_connection


class Command(BaseCommand):
    help = "Run the scheduler"

    def handle(self, *args, **options):
        wait_for_connection()
        initialize_messaging()

        scheduler = Beat(
            app=app,
            max_interval=60,
            scheduler=schedulers.DatabaseScheduler,
            loglevel=getenv("LOG_LEVEL", "INFO"),
        )
        scheduler.run()
