"""Database related stuff"""

import os

from pymongo import MongoClient
from pymongo.collection import Collection


def get_collection(collection: str) -> Collection:
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
