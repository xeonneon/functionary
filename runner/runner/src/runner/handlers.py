import json
import os
from time import sleep

import docker
import requests
from celery import Task

from .celery import app


class PluginClient(Task):
    REGISTRY = os.environ.get("REGISTRY", "localhost:5000")

    def __init__(self):
        self._docker = docker.from_env()


@app.task(base=PluginClient, bind=True)
def deploy_plugin(self, image_name: str) -> None:
    # image = self._docker.images.pull(image_name)
    print(f"Pulled {image_name}")


@app.task(base=PluginClient, bind=True)
def start_plugin(self, plugin_id: str) -> None:
    # self._docker.containers.get(plugin_id).start()
    print(f"Started plugin {plugin_id}")


@app.task(base=PluginClient, bind=True)
def stop_plugin(self, plugin_id: str) -> None:
    # self._docker.containers.get(plugin_id).stop()
    print(f"Stopped plugin {plugin_id}")


@app.task(base=PluginClient, bind=True)
def task_plugin(self, task):
    return _task_plugin_shell(self, task)
    # return _task_plugin_rest(self, task)


def _task_plugin_shell(client, task):
    plugin = task.get("plugin")
    fqi = f"{client.REGISTRY}/{plugin}"
    function = task.get("function")
    parameters = json.dumps(task["function_parameters"])
    run_command = ["--function", function, "--parameters", parameters]

    image = client._docker.images.pull(fqi)
    result = client._docker.containers.run(image, auto_remove=True, command=run_command)

    return f"{plugin}/{function} tasking complete: {result}"


def _task_plugin_rest(client, task):
    plugin = task.get("plugin")
    fqi = f"{client.REGISTRY}/{plugin}"
    plugin_id = task.get("plugin_id")
    function = task.get("function")
    payload = task["payload"]
    remove_after_tasking = True

    if plugin:
        image = client._docker.images.pull(fqi)
        container = client._docker.containers.run(
            image, detach=True, network="proto-network", auto_remove=True
        )
    elif plugin_id:
        container = client._docker.containers.get(plugin_id)
        remove_after_tasking = False
    else:
        raise Exception("Could not determine container")

    # give the container time to start (boo!)
    sleep(1)

    hostname = container.id[0:12]
    url = f"http://{hostname}:8000/functions/{function}"
    response = requests.post(url, data=json.dumps(payload))

    if remove_after_tasking:
        container.stop()

    return f"{plugin or plugin_id}/{function} tasking complete: {response.text}"
