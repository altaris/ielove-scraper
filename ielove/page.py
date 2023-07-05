"""Page scraping"""

from typing import Any, Dict
from urllib.parse import urlparse

import regex as re
from loguru import logger as logging

from ielove.utils import all_tag_contents, get_soup, process_string


def scrape_chintai(url: str) -> Dict[str, Any]:
    """
    Scrapes a chintai page, e.g.

        https://www.ielove.co.jp/chintai/c1-397758400
    """
    soup = get_soup(url)

    data: Dict[str, Any] = {}

    data["url"] = url
    data["pid"] = re.search(r"/([^/]+)/?$", urlparse(url).path).group(1)
    logging.debug("Scraping chintai page id '{}'", data["pid"])

    tags = soup.find_all(
        name="h1", class_="detail-summary__tatemononame ui-font--size_h1"
    )
    data["title"] = process_string(tags[0].contents[0])

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
