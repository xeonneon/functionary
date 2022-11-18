"""Helpers for interacting with the rabbitmq management api"""
from typing import Optional

import requests
from django.conf import settings

# TODO: Allow HTTPS connections
BASE_URL = f"http://{settings.RABBITMQ_HOST}:{settings.RABBITMQ_MANAGEMENT_PORT}/api"
USERNAME = settings.RABBITMQ_USER
PASSWORD = settings.RABBITMQ_PASSWORD


def create_vhost(name: str, description: Optional[str] = None) -> dict:
    """Create a virtual host

    Args:
      name: The name of the virtual host
      description: Description of the virtual host

    Returns:
      Dict containing the created virtual host's definition from the rabbitmq
      management server.
    """
    url = f"{BASE_URL}/vhosts/{name}"
    data = None

    if description is not None:
        data = {"description": description}

    requests.put(url, json=data, auth=(USERNAME, PASSWORD))
    vhost = requests.get(url, auth=(USERNAME, PASSWORD)).json()

    return vhost
