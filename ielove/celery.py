"""Celery app"""

import os
import sys

from celery import Celery


def is_worker() -> bool:
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
