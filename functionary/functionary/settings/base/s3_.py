from os import getenv

S3_HOST = getenv("MINIO_HOST")
S3_PORT = getenv("MINIO_PORT")
S3_REGION = getenv("MINIO_REGION")
S3_SECURE = False
S3_ACCESS_KEY = getenv("MINIO_ROOT_USER")
S3_SECRET_KEY = getenv("MINIO_ROOT_PASSWORD")
S3_SIGNED_URL_TIMEOUT_MINUTES = 1

# If you chose to use seconds, the minimum should be ~3 seconds to account
# for any latency between the task message being sent to the runner and the
# container being created.
S3_SIGNED_URL_TIMEOUT_SECONDS = 0
