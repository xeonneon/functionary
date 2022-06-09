from celery import Celery

app = Celery(
    "plugin_runner", broker="redis://redis", include=["plugin_runner.handlers"]
)


if __name__ == "__main__":
    app.start()
