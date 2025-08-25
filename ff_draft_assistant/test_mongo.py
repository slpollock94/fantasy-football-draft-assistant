#!/usr/bin/env python3
"""Test MongoDB connection and add sample data."""

import os
from dotenv import load_dotenv
from mongo_utils import insert_players, get_all_players, search_players

load_dotenv()

def test_mongo_connection():
    """Test MongoDB connection and basic operations."""
    print("Testing MongoDB connection...")
    
    # Test sample data
    sample_players = [
        {
            "rank": "1",
            "name": "Christian McCaffrey",
            "position": "RB",
            "team": "SF",
            "projected_points": 320.5,
            "avg_points": 18.5,
            "drafted": False
        },
        {
            "rank": "2", 
            "name": "Austin Ekeler",
            "position": "RB",
            "team": "LAC",
            "projected_points": 280.3,
            "avg_points": 16.2,
            "drafted": False
        },
        {
            "rank": "3",
            "name": "Cooper Kupp",
            "position": "WR", 
            "team": "LAR",
            "projected_points": 275.8,
            "avg_points": 15.9,
            "drafted": False
        }
    ]
    
    try:
        # Test insertion
        print("Inserting sample players...")
        insert_players(sample_players)
        
        # Test retrieval
        print("Retrieving all players...")
        all_players = get_all_players()
        print(f"Found {len(all_players)} players in database")
        
        # Test search
        print("Searching for RBs...")
        rbs = search_players({"position": "RB"})
        print(f"Found {len(rbs)} RBs")
        
        # Print sample results
        for player in all_players[:3]:
            print(f"  {player.get('rank', 'N/A')}. {player.get('name', 'Unknown')} ({player.get('position', 'N/A')} - {player.get('team', 'N/A')})")
            
        print("MongoDB connection test successful!")
        return True
        
    except Exception as e:
        print(f"MongoDB connection test failed: {e}")
        return False

if __name__ == "__main__":
    test_mongo_connection()
