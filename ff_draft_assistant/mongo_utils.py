import os
import logging
from typing import List, Dict

from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB", "fantasy_football")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION", "players")

if not MONGO_URI:
    raise ValueError("MONGO_URI not set in environment or .env file.")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

logger = logging.getLogger(__name__)


def insert_players(players: List[Dict]) -> None:
    """Insert or update player documents in MongoDB.

    Parameters
    ----------
    players: List[Dict]
        Player data to upsert into the collection.
    """

    if not players:
        logger.info("No players provided for insertion.")
        return

    inserted = 0
    updated = 0
    for player in players:
        filter_ = {"name": player.get("name"), "position": player.get("position")}
        result = collection.update_one(filter_, {"$set": player}, upsert=True)
        if result.matched_count:
            updated += 1
        else:
            inserted += 1

    logger.info("Inserted %d players, updated %d players", inserted, updated)

def search_players(query: Dict) -> List[Dict]:
    return list(collection.find(query, {"_id": 0}))

def get_all_players() -> List[Dict]:
    return list(collection.find({}, {"_id": 0}))

# Example usage:
# insert_players([{...}, {...}])
# print(search_players({"position": "RB"}))
# print(get_all_players())
