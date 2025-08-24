import os
import sys
import types
import pytest
from importlib import reload

# Provide minimal stubs if real packages are unavailable
sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda: None))

class DummyMongoClient:
    def __init__(self, uri):
        pass
    def __getitem__(self, name):
        return self

sys.modules.setdefault("pymongo", types.SimpleNamespace(MongoClient=DummyMongoClient))

os.environ["MONGO_URI"] = "mongodb://localhost:27017"
from ff_draft_assistant import mongo_utils as mongo_utils_module
mongo_utils = reload(mongo_utils_module)

class DummyCollection:
    def __init__(self):
        self.data = []

    def delete_many(self, _):
        self.data = []

    def insert_many(self, docs):
        self.data.extend(docs)

    def find(self, query, projection=None):
        def match(doc):
            for k, v in query.items():
                if doc.get(k) != v:
                    return False
            return True
        return [d for d in self.data if match(d)]

@pytest.fixture
def patched_mongo(monkeypatch):
    dummy = DummyCollection()
    monkeypatch.setattr(mongo_utils, "collection", dummy)
    return mongo_utils, dummy

def test_insert_search_get_all(patched_mongo):
    mu, dummy = patched_mongo
    players = [
        {"name": "A", "position": "RB"},
        {"name": "B", "position": "QB"},
    ]
    mu.insert_players(players)
    assert dummy.data == players
    assert mu.search_players({"position": "RB"}) == [{"name": "A", "position": "RB"}]
    assert mu.get_all_players() == players
