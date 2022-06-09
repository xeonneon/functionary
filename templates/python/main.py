import json

import click
from _plugin import functions


@click.command()
@click.option("--function", help="The plugin function to execute", required=True)
@click.option("--parameters", help="JSON str of parameters to pass to the function")
def main(function: str, parameters: str):
    parameters = parameters or "{}"
    result = getattr(functions, function)(**json.loads(parameters))

    print(result)


if __name__ == "__main__":
    main()
