from os import getenv

MINIO_HOST = getenv("MINIO_HOST")
MINIO_PORT = getenv("MINIO_PORT")
MINIO_SECURE = False
MINIO_ACCESS_KEY = getenv("MINIO_ROOT_USER")
MINIO_SECRET_KEY = getenv("MINIO_ROOT_PASSWORD")
MINIO_SIGNED_URL_TIMEOUT_MINUTES = 1

# If you chose to use seconds, the minimum should be ~3 seconds to account
# for any latency between the task message being sent to the runner and the
# container being created.
MINIO_SIGNED_URL_TIMEOUT_SECONDS = 0
