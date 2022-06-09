import json

from fastapi import FastAPI, HTTPException

from _plugin import functions
from _utils import function_list, function_schema, resolve_parameters

app = FastAPI()

with open("./_schema.json", "r") as file:
    app.openapi_schema = json.loads(file.read())


@app.get("/schema")
def get_spec():
    return app.openapi_schema


@app.post("/functions/{function_name}")
def post_call(function_name: str, request_body: dict):
    function = getattr(functions, function_name)
    parameters = resolve_parameters(function, request_body)

    try:
        return getattr(functions, function_name)(**parameters)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
