"""Page scraping"""

from datetime import datetime
from typing import Any, Dict, Union
from urllib.parse import urlparse, ParseResult

import regex as re
from loguru import logger as logging

from ielove.utils import all_tag_contents, get_soup, process_string


def scrape_property_page(url: Union[str, ParseResult]) -> Dict[str, Any]:
    """
    Scrapes a property page page, e.g.

        https://www.ielove.co.jp/chintai/c1-397758400
        https://www.ielove.co.jp/mansion_shinchiku/b1-404543984/
    """
    soup = get_soup(url)
    if isinstance(url, str):
        url = urlparse(url)

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

    tags = soup.find_all(name="div", class_="detail-spot__map")
    m = re.search(r"q=(\d+\.\d+),(\d+\.\d+)&", tags[0].iframe["data-src"])
    data["location"] = [float(m.group(1)), float(m.group(2))]

    return data


def scrape_result_page(url: str) -> Dict[str, Any]:
    """
    Scrapes all ids from a chintai result page, e.g.

        https://www.ielove.co.jp/chintai/tokyo/result/
        https://www.ielove.co.jp/mansion_chuko/tokyo/result/?pg=2

    Returns a dict. The list of propertu page ids is under the `pids` key.
    """
    logging.info("Scraping property result page '{}'", url)
    soup = get_soup(url)
    r = re.compile("^/[^/]+/(.+)/$")
    pids = []
    for tag in soup.find_all(name="a", class_="result-panel-room__inner"):
        pids.append(r.search(tag["href"]).group(1))
    data = {"_datetime": datetime.now(), "pids": pids}
    return data
