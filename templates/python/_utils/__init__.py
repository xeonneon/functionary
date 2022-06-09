import inspect
import json
import os
from typing import List

SCHEMA_DIR = "./_plugin/_schemas"


def function_list() -> List[str]:
    return list(map(lambda x: x.replace(".json", ""), os.listdir(SCHEMA_DIR)))


def function_schema(function_name) -> dict:
    with open(f"{SCHEMA_DIR}/{function_name}.json", mode="r") as file:
        return json.load(file)


def resolve_parameters(func, request_body: dict) -> dict:
    parameters = {}

    signature = inspect.signature(func)

    for name, param in signature.parameters.items():
        if name in request_body:
            value = request_body[name]

            if param.annotation.__module__ in ["builtins", "typing"]:
                parameters[name] = value
            else:
                parameters[name] = param.annotation(**value)

    return parameters
