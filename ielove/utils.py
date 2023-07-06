"""
General utilities
"""

import datetime
from typing import Any, Union
from urllib.parse import ParseResult

import bs4
import regex as re
import requests
from loguru import logger as logging


def all_tag_contents(tag: bs4.element.Tag) -> list:
    """Recursively extracts the content of every subtag"""
    results = []
    for c in tag.contents:
        if isinstance(c, str):
            results.append(process_string(c))
        elif isinstance(c, bs4.element.Tag):
            results += all_tag_contents(c)
        else:
            logging.warning(f"Unsupported tag content '{type(c)}': {c}")
    return results


def get_soup(url: Union[str, ParseResult]) -> bs4.BeautifulSoup:
    """Gets the HTML code of a page, parsed into a `bs4.BeautifulSoup`"""
    if isinstance(url, ParseResult):
        url = url.geturl()
    logging.debug("GET {}", url)
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return bs4.BeautifulSoup(response.text, "html.parser")


def process_string(x: str) -> Any:
    """
    Some string processing. Might returns something other than a string
    """
    replaces = [
        ("０", "0"),
        ("１", "1"),
        ("２", "2"),
        ("３", "3"),
        ("４", "4"),
        ("５", "5"),
        ("６", "6"),
        ("７", "7"),
        ("８", "8"),
        ("９", "9"),
        ("\n", " "),
        ("㎡", "m2"),
        ("、", ", "),
        ("！", "! "),
        ("。", ". "),
        ("　", " "),
        ("（", "("),
        ("）", ")"),
        ("［", "["),
        ("］", ")"),
    ]
    for a, b in replaces:
        x = x.replace(a, b)
    x = x.strip()
    if x == "-":
        return None
    if re.search(r"^\d+$", x):
        return int(x)
    if re.search(r"^\d+\.\d+$", x):
        return float(x)
    if m := re.search(r"(\d+)\s*年(\d+)\s*月(\d+)\s*日", x):
        year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return datetime.datetime(year, month, day)
    return x
