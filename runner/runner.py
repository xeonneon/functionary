import logging
import os

from runner import Listener, Worker

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=LOG_LEVEL)
logging.getLogger("pika").propagate = False


def spawn_listener():
    listener = Listener()
    listener.start()


def spawn_worker():
    worker = Worker()
    worker.start()


if __name__ == "__main__":
    spawn_listener()
    spawn_worker()

    logging.debug("Started worker and listener processes")
