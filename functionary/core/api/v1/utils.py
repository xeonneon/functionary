import json
import re
from collections import OrderedDict
from typing import Union

from django.core.files.uploadedfile import InMemoryUploadedFile

PREFIX = "param"
SEPARATOR = r"\."

r = re.compile(rf"^({PREFIX}){SEPARATOR}(\w+)$")


def parse_parameters(values: OrderedDict) -> None:
    """Mutate given values to move all `param.` arguments in parameters field"""
    _update_parameter_field_type(values)

    # Avoid dictionary changed size error by wrapping items in list
    for param, _ in list(values.items()):
        if not (valid_param := r.match(param)):
            continue

        value = values.pop(param)
        if type(value) == InMemoryUploadedFile:
            value = value.name

        values["parameters"][valid_param.group(2)] = value


def get_parameter_name(parameter: str) -> Union[re.Match, None]:
    return r.match(parameter)


def _update_parameter_field_type(values: OrderedDict) -> None:
    """Mutates the `parameters` field to a dictionary"""
    if not values.get("parameters"):
        values["parameters"] = {}
    elif type(values.get("parameters")) == str:
        values["parameters"] = json.loads(values["parameters"])
