"""Database related stuff"""

from pymongo import MongoClient
from pymongo.collection import Collection


def get_collection(collection: str, user: str, password: str) -> Collection:
    """Returns a collection handler (under database `ielove`)"""
    uri = f"mongodb://{user}:{password}@localhost:27017/"
    client: MongoClient = MongoClient(uri)
    return client["ielove"][collection]
