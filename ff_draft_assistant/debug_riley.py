#!/usr/bin/env python3
"""
Debug Riley Neal issue
"""

from mongo_utils import get_all_players
from player_search import PlayerSearchEngine
import sys

def debug_riley_neal():
    print("DEBUGGING RILEY NEAL ISSUE")
    print("=" * 50)
    
    # Step 1: Check raw database
    print("1. Checking raw database...")
    players = get_all_players()
    print(f"   Total players in database: {len(players)}")
    
    # Search for Riley Neal in raw data
    riley_in_db = []
    for player in players:
        name = str(player.get('name', ''))
        if 'riley' in name.lower() and 'neal' in name.lower():
            riley_in_db.append(player)
    
    print(f"   Riley Neal found in database: {len(riley_in_db)}")
    for player in riley_in_db:
        print(f"     - {player}")
    
    # Step 2: Create fresh search engine
    print("\n2. Creating fresh search engine...")
    search_engine = PlayerSearchEngine()
    
    # Check if it has cached data
    cache_size = len(search_engine.players_cache) if hasattr(search_engine, 'players_cache') else 0
    print(f"   Initial cache size: {cache_size}")
    
    # Force refresh
    print("\n3. Force refreshing cache...")
    search_engine.refresh_cache()
    cache_size_after = len(search_engine.players_cache)
    print(f"   Cache size after refresh: {cache_size_after}")
    
    # Search for Riley Neal in cache
    riley_in_cache = []
    for player in search_engine.players_cache:
        name = str(player.get('name', ''))
        if 'riley' in name.lower() and 'neal' in name.lower():
            riley_in_cache.append(player)
    
    print(f"   Riley Neal found in cache: {len(riley_in_cache)}")
    for player in riley_in_cache:
        print(f"     - {player.get('name')} ({player.get('position')} - {player.get('team')})")
    
    # Step 4: Test search function
    print("\n4. Testing search function...")
    search_results = search_engine.search_players(query="Riley Neal", max_results=10)
    print(f"   Search results for 'Riley Neal': {len(search_results)}")
    for player in search_results:
        name = player.get('name', '')
        if 'riley' in name.lower() and 'neal' in name.lower():
            print(f"     *** FOUND: {player.get('name')} ({player.get('position')} - {player.get('team')})")
        else:
            print(f"     - {player.get('name')} ({player.get('position')} - {player.get('team')})")
    
    # Step 5: Test general search that might include Riley Neal
    print("\n5. Testing general search (first 20 players)...")
    all_results = search_engine.search_players(query="", max_results=20)
    riley_in_search = []
    for player in all_results:
        name = str(player.get('name', ''))
        if 'riley' in name.lower() and 'neal' in name.lower():
            riley_in_search.append(player)
    
    print(f"   Riley Neal in first 20 search results: {len(riley_in_search)}")
    for player in riley_in_search:
        print(f"     *** FOUND: {player.get('name')} ({player.get('position')} - {player.get('team')})")
    
    print("\n" + "=" * 50)
    print("DEBUG COMPLETE")

if __name__ == "__main__":
    debug_riley_neal()