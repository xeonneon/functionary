import docker

client = docker.from_env()


def pull_image(repository: str, tag: str):
    return client.images.pull(repository, tag)


def launch_container(repository: str, tag: str):
    return client.containers.run(f"{repository}:{tag}", detach=True).name


def start_container(name: str):
    client.containers.get(name).start()


def stop_container(name: str):
    client.containers.get(name).stop()
