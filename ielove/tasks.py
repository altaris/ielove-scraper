# pylint: disable=missing-function-docstring
"""Celery tasks"""

from datetime import datetime, timedelta
from typing import Optional

from loguru import logger as logging

from ielove import db, ielove
from ielove.celery import app
from ielove.utils import url_or_pid_to_pid


def _next_scrape_datetime(data: dict) -> datetime:
    """Returns the next datetime from which a property should be rescraped"""
    if "次回更新予定日" not in data["details"]:
        return datetime.now() + timedelta(days=30)
    dt_next = data["details"]["次回更新予定日"] + timedelta(days=1)
    if dt_next <= datetime.now():
        # If in the past, set to next month
        dt_next = datetime.now() + timedelta(days=30)
    return dt_next


def _should_scrape(url: str) -> bool:
    """
    Returns `True` if the property has never been scraped, or if the current
    datatime is after that provided by `_next_scrape_datetime`.
    """
    pid = url_or_pid_to_pid(url)
    collection = db.get_collection("properties")
    data: Optional[dict] = collection.find_one({"pid": pid})
    if data is None:
        return True
    return datetime.now() >= _next_scrape_datetime(data)


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
    eta = _next_scrape_datetime(data)
    scrape_property_page.apply_async((url,), eta=eta)
    logging.debug(
        "Scheduling rescraping of property {} to {}", data["pid"], eta
    )


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
