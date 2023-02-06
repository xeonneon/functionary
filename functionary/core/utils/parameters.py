from collections import defaultdict, namedtuple

Parameter = namedtuple("Parameter", "type format", defaults=(None, None))


def parameter_mapping(schema: dict) -> dict[str, list[Parameter]]:
    """Helper function to get parameter types and formats

    Returns a dictionary keyed by the parameter arguments. The values are
    a list of namedtuple called `Parameter`, which includes the `type` and `format`
    information about each parameter in the function.

    Example outputs would be:

    `dict_items([('a', [Parameter(type='integer', format=None)]), \
        ('b', [Parameter(type='integer', format=None)])])`

    `dict_items([('file', [Parameter(type='string', format='uri'), \
        Parameter(type='string', format='binary')])])`

    Arguments:
        schema: The function schema

    Returns:
        parameters: A dictionary with the function parameter name
            and a list of corresponding `Parameter` tuples
    """
    parameters = defaultdict(list)
    for param_name, param_info in schema.get("properties").items():
        if param_meta := param_info.get("anyOf"):
            for param_type in param_meta:
                parameters[param_name].append(
                    Parameter(param_type.get("type"), param_type.get("format"))
                )
        else:
            parameters[param_name].append(Parameter(param_info.get("type"), None))
    return parameters
