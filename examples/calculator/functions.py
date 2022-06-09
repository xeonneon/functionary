from typing import Literal, Union


def add(a: int, b: int) -> int:
    return a + b


def subtract(a: int, b: int) -> int:
    return a - b


def multiply(a: int, b: int) -> int:
    return a * b


def divide(a: int, b: int) -> float:
    return a / b


def pick(a: int, b: int, operation: Literal["+", "-", "*", "/"]) -> Union[int, float]:
    match operation:
        case "+":
            return add(a, b)
        case "-":
            return subtract(a, b)
        case "*":
            return multiply(a, b)
        case "/":
            return divide(a, b)
        case _:
            raise Exception("Operation must be '+', '-', '*', or '/'.")
