import os
from pymongo import MongoClient
from typing import List, Dict
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

def insert_players(players: List[Dict]):
    if players:
        collection.delete_many({})  # Clear old data
        collection.insert_many(players)

def search_players(query: Dict) -> List[Dict]:
    return list(collection.find(query, {"_id": 0}))

def get_all_players() -> List[Dict]:
    return list(collection.find({}, {"_id": 0}))

# Example usage:
# insert_players([{...}, {...}])
# print(search_players({"position": "RB"}))
# print(get_all_players())
