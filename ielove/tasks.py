# pylint: disable=missing-function-docstring
"""Celery tasks"""

from urllib.parse import ParseResult

from loguru import logger as logging

from ielove import db, ielove
from ielove.celery import app

ONE_MONTH = 60 * 60 * 24 * 7 * 30  # Thirty days in seconds


def _should_scrape(url: str) -> bool:
    """Returns False if the page has been scraped within a week"""
    if isinstance(url, ParseResult):
        url = url.geturl()
    age = ielove.seconds_since_last_scrape(url)
    return not 0 < age < ONE_MONTH


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


@app.task(rate_limit="20/m")
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
