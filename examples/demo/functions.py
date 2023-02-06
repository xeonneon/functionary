import os
import time

import requests


def output_json(input: dict):
    """Demo JSON rendering by accepting JSON input and mirroring it back out"""
    return input


def output_text(input: str):
    """Demo text rendering by accepting string input and mirroring it back out. CSV
    formatted strings will present the option of rendering as a table"""
    return input


def long_running_process(duration: int = 60):
    """Simulates a long running process"""
    time.sleep(duration)


def variables():
    """Print environment variables that got passed through"""
    vars = []
    for name, value in os.environ.items():
        vars.append(f"{name}: {value}")

    output = "\n".join(vars)

    print(output)
    return [{"name": n, "value": v} for n, v in os.environ.items()]


def num_chars(file: str) -> int:
    print(f"Fetching file from this URL: {file}")
    request = requests.get(file)
    if request.status_code == 200:
        return len(request.text)
    return 0
