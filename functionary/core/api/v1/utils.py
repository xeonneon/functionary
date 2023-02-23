import json
import re
from collections import OrderedDict
from typing import Union

from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from core.models import Function, FunctionParameter
from core.utils.parameter import PARAMETER_TYPE

PREFIX = "param"
SEPARATOR = r"\."

r = re.compile(rf"^({PREFIX}){SEPARATOR}(\w+)$")


def parse_parameters(values: OrderedDict) -> None:
    """Mutate given values to move all `param.` arguments in parameters field"""
    _update_parameter_field_type(values)

    # Avoid dictionary changed size error by wrapping items in list
    for param, _ in list(values.items()):
        if not (valid_param := get_parameter_name(param)):
            continue

        value = values.pop(param)
        if type(value) == InMemoryUploadedFile:
            value = value.name

        values["parameters"][valid_param.group(2)] = value


def cast_parameters(values: OrderedDict) -> None:
    """Parent method to cast parameters to necessary types"""
    _cast_json_parameters(values)


def get_parameter_name(parameter: str) -> Union[re.Match, None]:
    """Return match if parameter name is of valid format"""
    return r.match(parameter)


def _cast_json_parameters(values: OrderedDict) -> None:
    """Mutates all JSON parameter fields into python objects

    Args:
        values: An OrderedDict containing the values passed to the serializer

    Returns:
        None

    Raises:
        ValidationError: When a JSON parameter is not valid JSON
    """
    function = _get_function(values)

    json_params: list[FunctionParameter] = [
        param
        for param in function.parameters.all()
        if param.parameter_type == PARAMETER_TYPE.JSON
    ]

    for json_param in json_params:
        try:
            if type(values["parameters"][json_param.name]) == dict:
                continue

            values["parameters"][json_param.name] = json.loads(
                values["parameters"][json_param.name]
            )
        except json.decoder.JSONDecodeError as err:
            exception_map = {json_param.name: err.msg}
            exc = ValidationError(exception_map)
            raise serializers.ValidationError(serializers.as_serializer_error(exc))


def _get_function(values: OrderedDict) -> Function:
    """Get the function from the internal values

    Fetch the Function object from the values dictionary. If the `function` key
    is not present, then we know the function name and package name serializer
    was used. Since that serializer does not substitute the Function before
    it's create method, we must fetch the function ourselves.

    Args:
        values: An ordered dict containing the values passed to the serializer

    Returns:
        function: The function object

    Raises:
        ValidationError: If the function was not found
    """
    try:
        if not (function := values.get("function")):
            function: Function = Function.objects.get(
                name=values.get("function_name"),
                package__name=values.get("package_name"),
            )
        return function
    except Function.DoesNotExist as err:
        exception_map = {"function_name": err}
        exc = ValidationError(exception_map)
        raise serializers.ValidationError(serializers.as_serializer_error(exc))


def _update_parameter_field_type(values: OrderedDict) -> None:
    """Mutates the `parameters` field to a dictionary"""
    if not values.get("parameters"):
        values["parameters"] = {}
    elif type(values.get("parameters")) == str:
        values["parameters"] = json.loads(values["parameters"])
