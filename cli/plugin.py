import json
import os
from pathlib import Path
from typing import Tuple

import typer
import yaml
from openapi import openapi_from_plugin

REGISTRY = "localhost:5000"
app = typer.Typer()


@app.command()
def create(language: str = typer.Option(...), name: str = typer.Argument(...)):
    image_map = {"python": "bgproto-python:latest"}

    image = image_map.get(language)

    if image is None:
        typer.echo(f"Language {language} is currently unsupported")
        raise typer.Abort()

    os.mkdir(name)
    metadata = {"name": name, "version": "1.0", "language": language}
    with open(f"{name}/plugin.yaml", mode="w") as file:
        file.write(yaml.dump(metadata))

    with open(f"{name}/requirements.txt", mode="w") as file:
        pass

    with open(f"{name}/functions.py", mode="w") as file:
        file.write(_get_example(language))


@app.command()
def build(path: Path) -> Tuple[str, str]:
    if not path.is_dir():
        typer.echo(f"Could not find directory {path}")
        raise typer.Abort()

    with open(f"{path}/plugin.yaml", mode="r") as file:
        metadata = yaml.safe_load(file)

    name = metadata["name"]
    version = metadata["version"]
    language = metadata["language"]
    dockerfile = _get_dockerfile(language)

    genschema(path)
    os.system(f"docker build -f {dockerfile} -t {REGISTRY}/{name}:{version} {path}")

    return (name, version)


@app.command()
def deploy(path: Path):
    name, version = build(path)
    os.system(f"docker push {REGISTRY}/{name}:{version}")


@app.command()
def genschema(path: Path):
    schema_file = "_schema.json"

    with open(schema_file, mode="w") as file:
        file.write(json.dumps(openapi_from_plugin(path), indent=2))


def _get_dockerfile(language: str):
    basepath = Path(__file__).parent.resolve()
    return f"{basepath}/docker/python.Dockerfile"


def _get_example(language: str):
    python_example = """def myfunc(a: int, b: int) -> int:
    return a + b\n"""

    return python_example


if __name__ == "__main__":
    app()
