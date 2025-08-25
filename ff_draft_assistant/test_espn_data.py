#!/usr/bin/env python3
"""Test ESPN data handling with mock data."""

import logging
from mongo_utils import insert_players

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_mock_espn_data():
    """Test with mock ESPN-style player data"""
    print("Testing with mock ESPN data...")
    
    # Create mock player data similar to what would come from ESPN
    mock_players = [
        {
            "rank": "1",
            "name": "Christian McCaffrey",
            "position": "RB",
            "team": "SF",
            "projected_points": 285.6,
            "avg_points": 18.4,
            "drafted": False,
            "source": "ESPN_Test"
        },
        {
            "rank": "2", 
            "name": "Josh Allen",
            "position": "QB",
            "team": "BUF",
            "projected_points": 312.8,
            "avg_points": 23.1,
            "drafted": False,
            "source": "ESPN_Test"
        },
        {
            "rank": "3",
            "name": "Tyreek Hill",
            "position": "WR", 
            "team": "MIA",
            "projected_points": 268.9,
            "avg_points": 16.8,
            "drafted": False,
            "source": "ESPN_Test"
        },
        {
            "rank": "4",
            "name": "Travis Kelce",
            "position": "TE",
            "team": "KC", 
            "projected_points": 198.5,
            "avg_points": 12.4,
            "drafted": False,
            "source": "ESPN_Test"
        },
        {
            "rank": "5",
            "name": "Cooper Kupp",
            "position": "WR",
            "team": "LAR",
            "projected_points": 245.3,
            "avg_points": 15.3,
            "drafted": False,
            "source": "ESPN_Test"
        }
    ]
    
    try:
        # Test inserting mock data
        logger.info(f"Inserting {len(mock_players)} mock ESPN players...")
        insert_players(mock_players)
        logger.info("Mock ESPN data insertion successful!")
        print(f"Successfully inserted {len(mock_players)} mock ESPN players")
        return True
        
    except Exception as e:
        logger.error(f"Error inserting mock ESPN data: {e}")
        print(f"Failed to insert mock ESPN data: {e}")
        return False

if __name__ == "__main__":
    test_mock_espn_data()
