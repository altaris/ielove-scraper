"""HTTP request utilities"""

from loguru import logger as logging
from requests.api import request
from requests.models import Response

from ielove.celery import app, is_worker


@app.task(rate_limit="20/m", serializer="pickle")
def _http_request(method: str, url: str, **kwargs) -> Response:
    """
    HTTP request wrapped as a Celery task. Don't use this directly, use
    `http_request` instead.
    """
    logging.debug("{} {}", method.upper(), url)
    # pylint: disable=missing-timeout
    response = request(method, url, **kwargs)
    # response.raise_for_status()
    return response


def get(url: str, **kwargs) -> Response:
    """Convenience function to issue a HTTP GET request. See `http_request`."""
    return http_request("get", url, **kwargs)


def http_request(method: str, url: str, **kwargs) -> Response:
    """
    Make an HTTP request. It is asynchronous if the current thread is a celery
    worker thread (see `ielove.celery.is_worker`), or syncronusly otherwise.
    """
    if is_worker():
        return _http_request.delay(method, url, **kwargs)
    return _http_request(method, url, **kwargs)


def post(url: str, **kwargs) -> Response:
    """
    Convenience function to issue a HTTP POST request. See `http_request`.
    """
    return http_request("post", url, **kwargs)
