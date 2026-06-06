import os
import atexit
from functools import lru_cache

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()


class Neo4jConfigurationError(Exception):
    pass


def is_neo4j_configured() -> bool:
    return all(
        os.getenv(name, "").strip()
        for name in ("NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD")
    )


@lru_cache
def get_neo4j_driver():
    uri = os.getenv("NEO4J_URI", "").strip()
    username = os.getenv("NEO4J_USERNAME", "").strip()
    password = os.getenv("NEO4J_PASSWORD", "").strip()
    if not all((uri, username, password)):
        raise Neo4jConfigurationError(
            "NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD must be configured"
        )
    return GraphDatabase.driver(uri, auth=(username, password))


def check_neo4j_connection() -> bool:
    driver = get_neo4j_driver()
    driver.verify_connectivity()
    record = driver.execute_query(
        "RETURN 1 AS connected",
        routing_="r",
    ).records[0]
    return record["connected"] == 1


def close_neo4j_driver() -> None:
    if get_neo4j_driver.cache_info().currsize:
        get_neo4j_driver().close()
        get_neo4j_driver.cache_clear()


atexit.register(close_neo4j_driver)
