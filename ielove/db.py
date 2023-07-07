"""Database related stuff"""

import os
from typing import List
from urllib.parse import urlparse

import pymongo
import regex as re
from pymongo import MongoClient
from pymongo.collection import Collection


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
    c = client["ielove"][collection]
    # TODO: ensure index
    # if collection == "properties":
    #     c.create_index([("$**", pymongo.TEXT), ("location", pymongo.GEO2D)])
    return c


def get_property(key: str, limit: int = 0) -> List[dict]:
    """
    Returns all recors of a property, sorted by most to least recent. Key can
    either be a URL pointing to the property or just the pid.
    """
    if key.startswith("http"):
        url = urlparse(key)
        key = re.search("/([^/]+)/?$", url.path).group(1)
    collection = get_collection("properties")
    result = collection.find(
        {"pid": key},
        sort=[("datetime", pymongo.DESCENDING)],
        limit=limit,
    )
    return list(result)
