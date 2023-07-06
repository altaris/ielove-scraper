# pylint: disable=import-outside-toplevel
"""Entry point"""
__docformat__ = "google"


import os
import sys

import click
from loguru import logger as logging
from rich.pretty import pprint

from ielove import ielove
from ielove.db import get_collection


def _setup_logging(logging_level: str = "INFO") -> None:
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
def get_property(url: str, commit: bool):
    """Scrapes a property page and prints the results"""
    data = ielove.scrape_property_page(url)
    pprint(data)
    if commit:
        collection = get_collection("properties")
        collection.insert_one(data)


@main.command()
@click.argument("url", type=str)
def get_properties(url: str):
    """
    Scrapes all property pages referenced by the given result page, and commits
    everything to database
    """
    data = ielove.scrape_result_page(url)
    collection = get_collection("properties")
    for page in data["pages"]:
        try:
            data = scrape_property_page(page["url"])
            collection.insert_one(data)
        except Exception as e:
            logging.error(f"{type(e)}: {str(e)}")


@main.command()
@click.argument("url", type=str)
def scrape_property_page(url: str):
    """Asynchronously scrapes property page and commits the results"""
    from ielove import tasks

    tasks.scrape_property_page.delay(url)


@main.command()
@click.argument("url", type=str)
def scrape_result_page(url: str):
    """
    Asynchronously scrapes all properties in a given result page, and commits
    the results
    """
    from ielove import tasks

    tasks.scrape_result_page.delay(url)


# pylint: disable=no-value-for-parameter
if __name__ == "__main__":
    main()
