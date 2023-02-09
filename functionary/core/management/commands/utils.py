from time import sleep
from typing import Callable

from django.db.utils import ProgrammingError

SLEEP_DURATION = 2


def run(command: Callable) -> None:
    """Run the given the command

    The given command will be executed to see if the necessary
    database migrations have been run. If the migrations have not
    been run, the command will be re-run after a delay.

    Args:
        command: The callable command to execute

    Returns:
        None
    """
    is_ready = False
    while not is_ready:
        try:
            command()
            is_ready = True
        except ProgrammingError:
            print("Migrations for the given command have not been run yet.")
            sleep(SLEEP_DURATION)
