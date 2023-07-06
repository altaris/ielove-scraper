"""Celery tasks"""

import os
import sys
from typing import Union
from urllib.parse import ParseResult

from celery import Celery

from ielove import ielove
from ielove.db import get_collection


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
    port = os.environ.get("REDIS_HOST", "6379")
    db = os.environ.get("REDIS_HOST", "0")
    uri = f"redis://{host}:{port}/{db}"
    return Celery("ielove.tasks", broker=uri)


app = get_app()


@app.task
def scrape_property_page(url: Union[str, ParseResult]) -> None:
    data = ielove.scrape_property_page(url)
    collection = get_collection("properties")
    collection.insert_one(data)
