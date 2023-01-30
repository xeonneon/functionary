import requests


def num_chars(file: str) -> int:
    request = requests.get(file)
    if request.status_code == 200:
        return len(request.text)
    return 0
