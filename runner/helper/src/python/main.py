import argparse
import json
import logging
import sys

from functions import *

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--function", help="the function to call")
    parser.add_argument(
        "-p",
        "--parameters",
        help="the parameters to pass to the function in JSON format",
    )

    args = parser.parse_args()
    params = json.loads(args.parameters)

    retVal = globals()[args.function](**params)

    print(f"==== Output From Command ====\n{str(retVal) if retVal else ''}")
