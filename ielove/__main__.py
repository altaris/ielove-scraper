"""
Entry point
"""
__docformat__ = "google"


import os
import sys
from datetime import datetime
from typing import Optional

import click
from loguru import logger as logging
from rich.pretty import pprint

from ielove.db import get_collection
from ielove.page import scrape_chintai


def _setup_logging(logging_level: str) -> None:
    """
    Sets logging format and level. The format is

        %(asctime)s [%(levelname)-8s] %(message)s

    e.g.

        2022-02-01 10:41:43,797 [INFO    ] Hello world
        2022-02-01 10:42:12,488 [CRITICAL] We're out of beans!

    Args:
        logging_level (str): Either 'critical', 'debug', 'error', 'info', or
            'warning', case insensitive. If invalid, defaults to 'info'.
    """
    logging.remove()
    logging.add(
        sys.stderr,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> "
            + "[<level>{level: <8}</level>] "
            + "<level>{message}</level>"
        ),
        level=logging_level.upper(),
        enqueue=True,
        colorize=True,
    )


@click.group()
@click.option(
    "--logging-level",
    default=os.getenv("LOGGING_LEVEL", "info"),
    help=(
        "Logging level, among 'critical', 'debug', 'error', 'info', and "
        "'warning', case insensitive."
    ),
    type=click.Choice(
        ["critical", "debug", "error", "info", "warning"],
        case_sensitive=False,
    ),
)
def main(logging_level: str):
    """Entrypoint."""
    _setup_logging(logging_level)


@main.command()
@click.option(
    "--commit/--no-commit",
    type=bool,
    help="Wether to commit the document to database",
    default=False,
)
@click.option("-u", "--user", type=str, help="MongoDB username", default=None)
@click.option(
    "-p", "--password", type=str, help="MongoDB password", default=None
)
@click.argument("url", type=str)
def get_chintai(
    url: str, commit: bool, user: Optional[str], password: Optional[str]
):
    """Scrapes a chintai page and prints the results"""
    data = scrape_chintai(url)
    pprint(data)
    if commit:
        if user is None or password is None:
            logging.error(
                "If commiting to database, user and password must be provided"
            )
            return
        data["_datetime"] = datetime.now()
        collection = get_collection("chintai", user, password)
        collection.insert_one(data)


# pylint: disable=no-value-for-parameter
if __name__ == "__main__":
    main()
