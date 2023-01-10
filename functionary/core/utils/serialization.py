from copy import deepcopy
from json import JSONDecodeError, dumps, loads
from typing import Union

# Place helper methods for serializing data that is used by the models in here
# Don't import any models to prevent cyclic module dependencies


def serialize_parameters(parameters: dict, schema: dict) -> Union[dict, None]:
    """JSON stringify parameters which are supposed to be JSON formatted strings

    Iterate throw the given schema to find any function arguments that
    could be JSON formatted strings. If so, dump the value of that argument
    into a JSON string, and overwrite that value in a deep copy of the
    given parameters dictionary.
    Perform the same logic if the function argument can be multiple different
    types, as indicated by 'anyOf'.
    Returns a deep copy of the parameters that contains all of the serialized
    JSON fields.

    NOTE: This function does not handle nested schemas past the function
    argument->anyOf[{}, {}, ...]. If the function schemas need to include more
    nesting, this will need to be reworked.

    Args:
        parameters: A dictionary that contains the parameters for the function.
            Example format looks like {'a': 1, 'b': 2}
        schema: A dictionary that represents the JSON schema for the function

    Returns:
        parameters: A new dictionary that contains all of the serialized
            function arguments.
    """
    if not parameters:
        return {}

    parameters_copy = deepcopy(parameters)
    try:
        for arg, param_type in schema["properties"].items():
            if union_type_param := param_type.get("anyOf"):
                serialize_union_parameters(arg, union_type_param, parameters_copy)
            else:
                if is_json_field(param_type):
                    parameters_copy[arg] = dumps(parameters_copy[arg])
                    # Validate the serialized JSON string is valid JSON
                    _ = loads(parameters_copy[arg])
        return parameters_copy
    except JSONDecodeError as err:
        raise err


def serialize_union_parameters(
    arg: str, union_type_param: dict, parameters: dict
) -> None:
    """Mutate given parameters dictionary to json stringify the parameters"""
    for param_type in union_type_param:
        if is_json_field(param_type):
            parameters[arg] = dumps(parameters[arg])
            _ = loads(parameters[arg])


def json_stringify_parameters(parameters: dict) -> str:
    """Turns the values of the dictionary keys into JSON strings

    Creates a new dictionary from the given dictionary and serializes each item
    for each key into a JSON string. This is necessary for the JSONField defined
    in the Task model.

    Args:
        parameters: A dictionary containing all the parameters for a Task

    Returns:
        params: A dictionary whose values are all JSON formatted strings

    Raises:
        JSONDecodeError: If one of the values in the parameters cannot be serialized
        into a JSON string, raise a JSONDecodeError
    """
    params = {}
    try:
        for key, value in parameters.items():
            json_stringified_params = dumps(value)
            params[key] = json_stringified_params
        return params
    except JSONDecodeError as err:
        raise err


def is_json_field(param: dict) -> bool:
    return "json-string" == param.get("format")
