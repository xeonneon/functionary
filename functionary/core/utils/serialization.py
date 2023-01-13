from copy import deepcopy
from json import JSONDecodeError, dumps

# Place helper methods for serializing data that is used by the models in here
# Don't import any models to prevent cyclic module dependencies


def serialize_parameters(parameters: dict, schema: dict) -> dict:
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

    Raises:
        JSONDecodeError: If a parameter is not valid JSON, a JSONDecodeError will
            be raised.
    """
    if not parameters:
        return {}

    parameters_copy = deepcopy(parameters)
    try:
        for arg, param_type in schema["properties"].items():
            if union_type_param := param_type.get("anyOf"):
                _serialize_union_parameters(arg, union_type_param, parameters_copy)
            else:
                if _is_json_field(param_type):
                    parameters_copy[arg] = dumps(parameters_copy[arg])
        return parameters_copy
    except JSONDecodeError as err:
        raise err


def _serialize_union_parameters(
    arg: str, union_type_param: dict, parameters: dict
) -> None:
    """Mutate given parameters dictionary to json stringify the parameters"""
    for param_type in union_type_param:
        if _is_json_field(param_type):
            parameters[arg] = dumps(parameters[arg])


def _is_json_field(param: dict) -> bool:
    return "json-string" == param.get("format")
