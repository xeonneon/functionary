import logging


def hello():
    print("Hello Docker World")


def hello_name(who="Docker"):
    logging.getLogger(__name__).info("Hello %s", who)
    return f"Hello {who}!"
