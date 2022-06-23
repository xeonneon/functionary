import json
import logging
import sys

import click
from functions import *

logging.basicConfig(level=logging.INFO, stream=sys.stdout)


@click.command()
@click.option("--function", "-f")
@click.option(
    "--parameters",
    "-p",
)
def runner(function, parameters):
    params = json.loads(parameters)

    retVal = globals()[function](**params)

    print(f"==== Output From Command ====\n{str(retVal) if retVal else ''}")


if __name__ == "__main__":
    runner()
