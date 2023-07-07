# pylint: disable=missing-function-docstring
"""Celery tasks"""

import os
import sys
from typing import Union
from urllib.parse import ParseResult

from celery import Celery

from ielove import ielove, db

ONE_MONTH = 60 * 60 * 24 * 7 * 30  # Thirty days in seconds


def _is_worker() -> bool:
    """Self explanatory. Credits to https://stackoverflow.com/a/50843002"""
    return (
        len(sys.argv) > 0
        and sys.argv[0].endswith("celery")
        and ("worker" in sys.argv)
    )


def _should_scrape(url: Union[str, ParseResult]) -> bool:
    """Returns False if the page has been scraped within a week"""
    if isinstance(url, ParseResult):
        url = url.geturl()
    age = ielove.seconds_since_last_scrape(url)
    return not 0 < age < ONE_MONTH


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
    if not _should_scrape(url):
        return
    data = ielove.scrape_property_page(url)
    collection = db.get_collection("properties")
    collection.find_one_and_replace({"pid": data["pid"]}, data, upsert=True)


@app.task(rate_limit="1/s")
def scrape_result_page(url: Union[str, ParseResult]) -> None:
    data = ielove.scrape_result_page(url)
    for page in data["pages"]:
        url = page["url"]
        if _should_scrape(url):
            scrape_property_page.delay(url)


@app.task
def scrape_region(region: str, property_type: str, limit: int = 100) -> None:
    base = f"https://www.ielove.co.jp/{property_type}/{region}/result"
    for i in range(1, limit + 1):
        url = f"{base}/?pg={i}"
        scrape_result_page.delay(url)
