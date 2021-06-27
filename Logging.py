import logging
from rich.logging import RichHandler


def log_setup(t):
    FORMAT = "%(message)s"
    logging.basicConfig(level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()])

    return logging.getLogger(t)
