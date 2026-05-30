import os
from functools import lru_cache

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "career_assistant")


@lru_cache
def get_mongodb_client():
    return MongoClient(
        MONGODB_URL,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
    )


def get_mongodb_database():
    return get_mongodb_client()[MONGODB_DATABASE]


def check_mongodb_connection():
    client = get_mongodb_client()
    result = client.admin.command("ping")
    return result["ok"] == 1.0
