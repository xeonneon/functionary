from datetime import datetime
from time import sleep
from typing import Optional

from pydantic import BaseModel


class AlarmResult(BaseModel):
    start: datetime
    end: datetime
    message: str


def add(a: int, b: int) -> int:
    return a + b


def concat(a: str, b: str) -> str:
    return a + b


def greet(name: str = "John Doe") -> str:
    return f"Hello {name}!"


def alarm(seconds: int, message: Optional[str] = None) -> AlarmResult:
    message = message or f"{seconds} seconds are up. Time to wake up!"
    start_time = datetime.now()
    sleep(seconds)
    end_time = datetime.now()

    return {"start": start_time, "end": end_time, "message": message}
