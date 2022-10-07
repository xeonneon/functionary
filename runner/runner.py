import logging
import sys
from os import getenv

from runner import Listener, Worker

LOG_LEVEL = getenv("LOG_LEVEL", "INFO")
logging.basicConfig(stream=sys.stdout, level=LOG_LEVEL)


def spawn_listener() -> Listener:
    listener = Listener()
    listener.start()

    return listener


def spawn_worker() -> Worker:
    worker = Worker()
    worker.start()

    return worker


if __name__ == "__main__":
    listener = spawn_listener()
    worker = spawn_worker()

    logging.debug("Started worker and listener processes")

    # Explicitly wait on the processes, otherwise when debugging the main process will
    # immediately exit.
    listener.join()
    worker.join()
