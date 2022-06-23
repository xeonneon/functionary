import json
import logging
import sys

from functions import *

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

if __name__ == "__main__":
    validParams = ["--function", "--parameters"]
    args = sys.argv[1:]

    if len(args) != 4 or args[0] not in validParams or args[2] not in validParams:
        print(
            "Invalid commandline, --function <function_name> "
            "--parameters <parameters in JSON format>"
        )
        sys.exit(1)

    toCall = parameters = None
    toCall = args[1] if args[0] == "--function" else args[3]
    parameters = json.loads(args[3] if args[2] == "--parameters" else args[1])

    retVal = globals()[toCall](**parameters)

    print(f"==== Output From Command ====\n{str(retVal) if retVal else ''}")
