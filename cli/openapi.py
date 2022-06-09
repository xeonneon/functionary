import inspect
import sys
from pathlib import Path

import yaml
from pydantic import BaseModel, create_model, schema_of


def openapi_from_plugin(path: Path):
    schemas = {}
    components = {"schemas": schemas}
    info = _plugin_info(path)
    paths = {}

    module = _plugin_module(path)
    functions = _function_list(module)

    for function in functions:
        _process_function(function, paths, schemas)

    spec = {
        "openapi": "3.0.0",
        "info": info,
        "paths": paths,
        "components": components,
    }

    return spec


def _function_list(module):
    return [
        getattr(module, func)
        for func in filter(
            lambda x: not x.startswith("_") and inspect.isfunction(getattr(module, x)),
            dir(module),
        )
    ]


def _function_schema(func) -> dict:
    signature = inspect.signature(func)
    parameters = {}

    for name, param in signature.parameters.items():
        default = param.default if param.default is not inspect._empty else ...
        parameters[name] = (param.annotation, default)

    return create_model(func.__name__, **parameters).schema()


def _plugin_info(path):
    with open(f"{path}/plugin.yaml", mode="r") as file:
        metadata = yaml.safe_load(file)

    info = {
        "title": metadata["name"],
        "description": metadata.get("description"),
        "version": metadata["version"],
        "x-language": metadata["language"],
    }

    return info


def _plugin_module(path):
    sys.path.append(str(path))

    import functions

    return functions


def _process_function(function, paths, schemas):
    schema_name = f"{function.__name__}_input"
    schema = _function_schema(function)
    definitions = schema.get("definitions", {})

    for name, object_def in definitions.items():
        _fix_refs(object_def)
        schemas[name] = object_def

    _ = schema.pop("definitions", None)

    _fix_refs(schema)
    schemas[schema_name] = schema

    response_schema = _generate_response_schema(function, schemas)

    paths[f"/functions/{function.__name__}"] = {
        "post": {
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": f"#/components/schemas/{schema_name}"}
                    }
                },
            },
            "responses": {
                "200": {"content": {"application/json": {"schema": response_schema}}}
            },
        }
    }


def _fix_refs(object_def):
    properties = object_def.get("properties", {})

    for _, prop in properties.items():
        prop_with_ref = None

        if "$ref" in prop:
            prop_with_ref = prop
        elif "items" in prop and "$ref" in prop["items"]:
            prop_with_ref = prop["items"]

        if prop_with_ref:
            ref = prop_with_ref["$ref"]
            prop_with_ref["$ref"] = ref.replace("#/definitions", "#/components/schemas")


def _generate_response_schema(function, schemas):
    return_type = inspect.get_annotations(function).get("return", str)

    is_pydantic = False

    try:
        is_pydantic = issubclass(return_type, BaseModel)
    except Exception:
        pass

    if is_pydantic:
        if return_type.__name__ not in schemas:
            for name, object_def in schema_of(return_type)["definitions"].items():
                _fix_refs(object_def)
                schemas[name] = object_def

        return {"$ref": f"#/components/schemas/{return_type.__name__}"}
    else:
        return schema_of(return_type)
