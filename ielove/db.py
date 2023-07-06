"""Database related stuff"""

import os

from pymongo import MongoClient
from pymongo.collection import Collection


def get_collection(collection: str) -> Collection:
    """Returns a collection handler (under database `ielove`)"""
    user = os.environ.get("MONGO_USER")
    password = os.environ.get("MONGO_PASSWORD")
    if user is None or password is None:
        raise RuntimeError(
            "MongoDB connection parameters not set. Set the MONGO_USER and "
            "MONGO_PASSWORD environment variables"
        )
    uri = f"mongodb://{user}:{password}@localhost:27017/"
    client: MongoClient = MongoClient(uri)
    return client["ielove"][collection]
