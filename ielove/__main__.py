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
from ielove.page import scrape_property_page, scrape_result_page


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
@click.argument("url", type=str)
def get_property(
    url: str, commit: bool
):
    """Scrapes a property page and prints the results"""
    data = scrape_property_page(url)
    pprint(data)
    if commit:
        collection = get_collection("property")
        collection.insert_one(data)


@main.command()
@click.option("-u", "--user", type=str, help="MongoDB username")
@click.option("-p", "--password", type=str, help="MongoDB password")
@click.argument("url", type=str)
def get_properties(url: str, user: str, password: str):
    """
    Scrapes all property pages referenced by the given result page, and commits
    everything to database
    """
    pids = scrape_result_page(url)["pids"]
    collection = get_collection("property", user, password)
    for pid in pids:
        try:
            url = f"https://www.ielove.co.jp/property/{pid}"
            data = scrape_property_page(url)
            collection.insert_one(data)
        except Exception as e:
            logging.error(f"{type(e)}: {str(e)}")


# pylint: disable=no-value-for-parameter
if __name__ == "__main__":
    main()
