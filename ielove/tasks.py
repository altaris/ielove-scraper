"""Celery tasks"""

import os
import sys
from typing import Union
from urllib.parse import ParseResult
import bs4

from celery import Celery
from loguru import logger as logging

from ielove import ielove, db, utils

ONE_WEEK = 60 * 60 * 24 * 7  # One week in seconds


def _is_worker() -> bool:
    """Self explanatory. Credits to https://stackoverflow.com/a/50843002"""
    return (
        len(sys.argv) > 0
        and sys.argv[0].endswith("celery")
        and ("worker" in sys.argv)
    )


def get_app() -> Celery:
    """Returns a celery app instance"""
    host = os.environ.get("REDIS_HOST", "localhost")
    port = os.environ.get("REDIS_PORT", "6379")
    k = os.environ.get("REDIS_DB", "0")
    uri = f"redis://{host}:{port}/{k}"
    return Celery("ielove.tasks", broker=uri)


app = get_app()


@app.task(rate_limit="1/s")
def scrape_property_page(url: Union[str, ParseResult]) -> None:
    age = ielove.seconds_since_last_scrape(url)
    if 0 < age < ONE_WEEK:
        logging.info(
            "Property page '{}' was scraped too recently ({}s ago), skipping",
            url,
            age,
        )
        return
    data = ielove.scrape_property_page(url)
    collection = db.get_collection("properties")
    collection.insert_one(data)


@app.task
def scrape_result_page(url: Union[str, ParseResult]) -> None:
    data = ielove.scrape_result_page(url)
    for page in data["pages"]:
        scrape_property_page.delay(page["url"])
