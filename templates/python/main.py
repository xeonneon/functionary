import argparse
import json
import logging
import sys

import functions

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

    retVal = getattr(functions, args.function)(**json.loads(args.parameters))

    print(f"==== Output From Command ====\n{str(retVal) if retVal else ''}")
