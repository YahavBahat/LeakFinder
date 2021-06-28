import logging
from rich.logging import RichHandler
from rich.text import Text


def log_setup(t):
    FORMAT = "%(message)s"
    logging.basicConfig(level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler(markup=True)])

    return logging.getLogger(t)


def get_underline(text):
    text = Text(text)
    text.stylize("underline")
    return text


def no_connection(text):
    return f"Couldn't establish connection for [underline]{text}[/underline]\n"


def successfully_authenticated(host, user, password):
    return f"Successfully authenticated for [underline]{host}[/underline] with user: [underline]{user}[/underline] " \
           f"and password: [underline]{password}[/underline]\n "
