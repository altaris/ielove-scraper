"""Database related stuff"""

import os
from typing import List, Optional

import pymongo
import regex as re
from pymongo import MongoClient
from pymongo.collection import Collection

from ielove.utils import url_or_pid_to_pid


def ensure_indices():
    """Ensures that search indices exist"""
    collection = get_collection("properties")
    indices = [  # name, field, type, kwargs
        ("pid", "pid", pymongo.ASCENDING, {"unique": True}),
        ("text", "$**", pymongo.TEXT, {}),
        ("location", "location.geo", pymongo.GEO2D, {}),
    ]
    info = collection.index_information()
    for a, b, c, d in indices:
        if a not in info:
            collection.create_index([(b, c)], name=a, **d)


def get_collection(collection: str = "properties") -> Collection:
    """Returns a collection handler (under database `ielove`)"""
    user, pswd = os.environ.get("MONGO_USER"), os.environ.get("MONGO_PASSWORD")
    host = os.environ.get("MONGO_HOST", "localhost")
    port = os.environ.get("MONGO_PORT", "27017")
    if user is None or pswd is None:
        raise RuntimeError(
            "MongoDB connection parameters not set. Set the MONGO_USER and "
            "MONGO_PASSWORD environment variables"
        )
    uri = f"mongodb://{user}:{pswd}@{host}:{port}/"
    client: MongoClient = MongoClient(uri)
    return client["ielove"][collection]


def get_property(key: str) -> Optional[dict]:
    """
    Returns a property document, or `None` if not found in the database. This
    method does not scrape.

    Args:
        key (str): Either a ielove URL, ielove ID, or a 物件管理番号 (in a
            string)
    """
    collection = get_collection("properties")
    if re.match(r"^\d+$", key):  # 物件管理番号
        return collection.find_one({"details.物件管理番号": int(key)})
    key = url_or_pid_to_pid(key)
    return collection.find_one({"pid": key})


def search_properties(text: str, limit: int = 20) -> List[dict]:
    """Full-text search against the collection of all properties"""
    collection = get_collection("properties")
    results = collection.find(
        {
            "$text": {
                "$search": text.strip(),
                "$caseSensitive": False,
                "$diacriticSensitive": False,
            }
        },
        limit=limit,
    )
    return list(results)
