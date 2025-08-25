import os
import logging
from typing import List, Dict
import ssl

from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB", "fantasy_football")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION", "players")

if not MONGO_URI:
    raise ValueError("MONGO_URI not set in environment or .env file.")

# Try different SSL configurations for MongoDB Atlas connection
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
except Exception:
    try:
        # Try with SSL context
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, ssl_context=ssl_context)
    except Exception:
        # Fallback: disable TLS altogether (not recommended for production)
        print("Warning: Using insecure connection to MongoDB")
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, tls=False)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

logger = logging.getLogger(__name__)

# Try to connect to MongoDB, fall back to local storage if needed
mongodb_available = False
try:
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    # Test the connection
    client.admin.command('ping')
    mongodb_available = True
    logger.info("MongoDB connection successful")
except Exception as e:
    logger.warning(f"MongoDB connection failed: {e}")
    logger.info("Falling back to local JSON storage")
    from local_store import LocalDataStore
    local_store = LocalDataStore()


def insert_players(players: List[Dict]) -> None:
    """Insert or update player documents in MongoDB or local storage.

    Parameters
    ----------
    players: List[Dict]
        Player data to upsert into the collection.
    """

    if not players:
        logger.info("No players provided for insertion.")
        return

    if mongodb_available:
        try:
            inserted = 0
            updated = 0
            for player in players:
                filter_ = {"name": player.get("name"), "position": player.get("position")}
                result = collection.update_one(filter_, {"$set": player}, upsert=True)
                if result.matched_count:
                    updated += 1
                else:
                    inserted += 1

            logger.info("Inserted %d players, updated %d players in MongoDB", inserted, updated)
        except Exception as e:
            logger.error("Failed to insert players into MongoDB: %s", e)
            raise
    else:
        local_store.insert_players(players)

def search_players(query: Dict) -> List[Dict]:
    if mongodb_available:
        try:
            return list(collection.find(query, {"_id": 0}))
        except Exception as e:
            logger.error("Failed to search players in MongoDB: %s", e)
            return []
    else:
        return local_store.search_players(query)

def get_all_players() -> List[Dict]:
    if mongodb_available:
        try:
            return list(collection.find({}, {"_id": 0}))
        except Exception as e:
            logger.error("Failed to retrieve players from MongoDB: %s", e)
            return []
    else:
        return local_store.get_all_players()

def update_player_drafted_status(player_name: str, drafted: bool) -> bool:
    """Update a player's drafted status.
    
    Parameters
    ----------
    player_name: str
        Name of the player to update
    drafted: bool
        New drafted status
        
    Returns
    -------
    bool
        True if update was successful, False otherwise
    """
    if mongodb_available:
        try:
            result = collection.update_one(
                {"name": player_name},
                {"$set": {"drafted": drafted}}
            )
            if result.matched_count > 0:
                logger.info(f"Updated drafted status for {player_name} to {drafted}")
                return True
            else:
                logger.warning(f"Player {player_name} not found in database")
                return False
        except Exception as e:
            logger.error(f"Failed to update player drafted status: {e}")
            return False
    else:
        return local_store.update_player_drafted_status(player_name, drafted)

# Example usage:
# insert_players([{...}, {...}])
# print(search_players({"position": "RB"}))
# print(get_all_players())
