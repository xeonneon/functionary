from .base import *  # noqa

DEBUG = False

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]


# TODO: Deploy another container to serve the staticfiles, or use whitenoise
STATIC_ROOT = f"{BASE_DIR}/static"
