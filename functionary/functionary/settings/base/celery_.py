"""Celery related settings"""
from os import getenv

RABBITMQ_HOST = getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = getenv("RABBITMQ_PORT", 5672)
RABBITMQ_USER = getenv("RABBITMQ_USER", "user")
RABBITMQ_PASSWORD = getenv("RABBITMQ_PASSWORD", "password")
RABBITMQ_VHOST = getenv("RABBITMQ_FUNCTIONARY_VHOST", "functionary")
CELERY_BROKER_URL = (
    f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}"
)
