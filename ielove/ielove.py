"""Page scraping"""

from base64 import b64encode
from datetime import datetime
from typing import Any, Dict, Iterable, Union
from urllib.parse import ParseResult, urlparse

import pymongo
import regex as re
import requests
from loguru import logger as logging

from ielove.db import get_collection
from ielove.utils import all_tag_contents, get_soup, process_string

ALL_REGIONS = [
    "aichi",
    "aichi",
    "akita",
    "aomori",
    "chiba",
    "chiba",
    "ehime",
    "fukui",
    "fukuoka",
    "fukuoka",
    "fukushima",
    "gifu",
    "gunma",
    "hiroshima",
    "hokkaido",
    "hokkaido",
    "hyogo",
    "ibaraki",
    "ishikawa",
    "iwate",
    "kagawa",
    "kagoshima",
    "kanagawa",
    "kanagawa",
    "kochi",
    "kumamoto",
    "kyoto",
    "mie",
    "miyagi",
    "miyazaki",
    "nagano",
    "nagasaki",
    "nara",
    "niigata",
    "oita",
    "okayama",
    "osaka",
    "osaka",
    "osaka",
    "saga",
    "saitama",
    "saitama",
    "shiga",
    "shimane",
    "shizuoka",
    "tochigi",
    "tokushima",
    "tokyo",
    "tokyo",
    "tokyo",
    "tottori",
    "toyama",
    "wakayama",
    "yamagata",
    "yamaguchi",
    "yamanashi",
]
ALL_PROPERTY_TYPES = [
    "chintai",
    "kodate_chuko",
    "kodate_shinchiku",
    "mansion_chuko",
    "mansion_shinchiku",
    "tochi",
]


# pylint: disable=too-many-locals
def scrape_property_page(url: Union[str, ParseResult]) -> Dict[str, Any]:
    """
    Scrapes a property page page, e.g.

        https://www.ielove.co.jp/chintai/c1-397758400
        https://www.ielove.co.jp/mansion_shinchiku/b1-404543984/
    """
    if isinstance(url, str):
        url = urlparse(url)
    soup = get_soup(url)

    m = re.search("^/?([^/]+)/([^/]+)/?$", url.path)
    data: Dict[str, Any] = {
        "url": url.geturl(),
        "pid": m.group(2),
        "type": m.group(1),
        "datetime": datetime.now(),
    }

    logging.info("Scraping {} page id '{}'", data["type"], data["pid"])

    tags = soup.find_all(
        name="h1", class_="detail-summary__tatemononame ui-font--size_h1"
    )
    data["name"] = process_string(tags[0].contents[0])

    tags = soup.find_all(name="p", class_="detail-salespoint__txt")
    data["salespoint"] = process_string(tags[0].contents[0])

    tags = soup.find_all(name="div", class_="detail-bkninfo__block")
    data["details"] = {}
    for tag in tags:
        hs = tag.find_all(name="dt", class_="detail-bkninfo__head")
        ts = tag.find_all(name="dd", class_="detail-bkninfo__txt")
        for h, t in zip(hs, ts):
            hc, tc = process_string(h.contents[0]), all_tag_contents(t)
            if len(tc) == 0:
                data["details"][hc] = None
            elif len(tc) == 1:
                data["details"][hc] = tc[0]
            else:
                data["details"][hc] = " ".join(map(str, tc))

    data["location"] = {}
    tags = soup.find_all(name="div", class_="detail-spot__map")
    if m := re.search(r"q=(\d+\.\d+),(\d+\.\d+)&", tags[0].iframe["data-src"]):
        data["location"]["geo"] = [float(m.group(1)), float(m.group(2))]
    if "住所" in data["details"]:
        r = r"(\w+[都道府県])?\s*(\w+[市町村])?\s*(\w+[区])?\s*(.*?)\s*(?:地図)?$"
        if m := re.search(r, data["details"]["住所"]):
            _f = lambda x: x if x else "-"
            a, b, c, d = m.groups()
            a, b, c, d = _f(a), _f(b), _f(c), _f(d)
            data["location"]["prefecture"] = a
            data["location"]["city"] = b
            data["location"]["ward"] = c
            data["location"]["address"] = d
            data["details"]["住所"] = f"{a} {b} {c} {d}"

    for tag in soup.find_all(name="img", class_="detail-thumbimage__img"):
        if "間取り" not in tag["alt"]:
            continue
        try:
            response = requests.get(tag["src"], timeout=10)
            response.raise_for_status()
            data["floor_plan"] = {
                "url": tag["src"],
                "img": b64encode(response.content),
            }
        except (requests.HTTPError, requests.Timeout) as e:
            logging.error(
                f"Could not get floor plan for property id {data['pid']} "
                f"({data['url']}): {type(e)} {str(e)}"
            )
        break

    return data


def scrape_result_page(url: Union[str, ParseResult]) -> Dict[str, Any]:
    """
    Scrapes all ids from a chintai result page, e.g.

        https://www.ielove.co.jp/chintai/tokyo/result/
        https://www.ielove.co.jp/mansion_chuko/tokyo/result/?pg=2

    If `soup` is provided, no additional GET against `ielove.co.jp` is issued.
    """
    if isinstance(url, ParseResult):
        url = url.geturl()
    logging.info("Scraping property result page '{}'", url)
    soup = get_soup(url)
    r = re.compile("^/(.+)/(.+)/$")
    pages = []
    for tag in soup.find_all(name="a", class_="result-panel-room__inner"):
        href = tag["href"]
        m = r.search(href)
        pages.append(
            {
                "pid": m.group(2),
                "type": m.group(1),
                "url": "https://www.ielove.co.jp" + href,
            }
        )
    data = {"datetime": datetime.now(), "pages": pages}
    return data


def seconds_since_last_scrape(url: Union[str, ParseResult]) -> int:
    """
    Returns the time (in seconds) since last time the property page was
    scraped. Returns -1 if the page was never scraped
    """
    collection = get_collection("properties")
    result: Iterable[dict] = collection.find(
        {"url": url},
        projection=["datetime"],
        sort=[("datetime", pymongo.DESCENDING)],
        limit=1,
    )
    result = list(result)
    if not result:
        return -1
    dt = result[0]["datetime"]
    return (datetime.now() - dt).seconds
