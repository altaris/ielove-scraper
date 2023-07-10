# pylint: disable=missing-function-docstring
"""Celery tasks"""

import os
import sys
from urllib.parse import ParseResult

from celery import Celery
from loguru import logger as logging

from ielove import db, ielove

ONE_MONTH = 60 * 60 * 24 * 7 * 30  # Thirty days in seconds


def _is_worker() -> bool:
    """Self explanatory. Credits to https://stackoverflow.com/a/50843002"""
    return (
        len(sys.argv) > 0
        and sys.argv[0].endswith("celery")
        and ("worker" in sys.argv)
    )


def _should_scrape(url: str) -> bool:
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


@app.task(rate_limit="20/m")
def scrape_property_page(url: str) -> None:
    if not _should_scrape(url):
        logging.debug(
            "Property page '{}' has been scraped too recently, skipping", url
        )
        return
    data = ielove.scrape_property_page(url)
    collection = db.get_collection("properties")
    collection.find_one_and_replace({"pid": data["pid"]}, data, upsert=True)


@app.task(rate_limit="20/m")
def scrape_result_page(url: str) -> None:
    data = ielove.scrape_result_page(url)
    for page in data["pages"]:
        url = page["url"]
        if _should_scrape(url):
            scrape_property_page.delay(url)


@app.task
def scrape_region(
    region: str, property_type: str, limit: int = 1000000
) -> None:
    url = f"https://www.ielove.co.jp/{property_type}/{region}/result/"
    try:
        last_page_idx = ielove.last_result_page_idx(url)
    except Exception as e:
        logging.warning(
            "Could not determine last result page index for property type "
            "'{}' in region '{}': {} {}",
            property_type,
            region,
            type(e),
            str(e),
        )
        last_page_idx = limit
    limit = min(last_page_idx, limit)
    for i in range(1, limit + 1):
        scrape_result_page.delay(f"{url}?pg={i}")
