#!/usr/bin/env python3
"""Enhanced ESPN data population with mock data fallback."""

import logging
import os
from mongo_utils import insert_players

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_comprehensive_mock_espn_data():
    """Create comprehensive mock ESPN player data for testing"""
    return [
        # Top QBs
        {"rank": "1", "name": "Josh Allen", "position": "QB", "team": "BUF", "projected_points": 312.8, "avg_points": 23.1, "drafted": False, "source": "ESPN_Mock"},
        {"rank": "6", "name": "Jalen Hurts", "position": "QB", "team": "PHI", "projected_points": 298.4, "avg_points": 22.2, "drafted": False, "source": "ESPN_Mock"},
        {"rank": "12", "name": "Lamar Jackson", "position": "QB", "team": "BAL", "projected_points": 285.6, "avg_points": 21.4, "drafted": False, "source": "ESPN_Mock"},
        {"rank": "18", "name": "Patrick Mahomes", "position": "QB", "team": "KC", "projected_points": 279.3, "avg_points": 20.8, "drafted": False, "source": "ESPN_Mock"},
        
        # Top RBs
        {"rank": "2", "name": "Christian McCaffrey", "position": "RB", "team": "SF", "projected_points": 285.6, "avg_points": 18.4, "drafted": False, "source": "ESPN_Mock"},
        {"rank": "3", "name": "Austin Ekeler", "position": "RB", "team": "LAC", "projected_points": 280.3, "avg_points": 16.2, "drafted": False, "source": "ESPN_Mock"},
        {"rank": "5", "name": "Derrick Henry", "position": "RB", "team": "TEN", "projected_points": 265.8, "avg_points": 15.8, "drafted": False, "source": "ESPN_Mock"},
        {"rank": "7", "name": "Jonathan Taylor", "position": "RB", "team": "IND", "projected_points": 258.9, "avg_points": 15.2, "drafted": False, "source": "ESPN_Mock"},
        {"rank": "10", "name": "Saquon Barkley", "position": "RB", "team": "NYG", "projected_points": 245.6, "avg_points": 14.8, "drafted": False, "source": "ESPN_Mock"},
        
        # Top WRs
        {"rank": "4", "name": "Cooper Kupp", "position": "WR", "team": "LAR", "projected_points": 268.9, "avg_points": 16.8, "drafted": False, "source": "ESPN_Mock"},
        {"rank": "8", "name": "Tyreek Hill", "position": "WR", "team": "MIA", "projected_points": 255.4, "avg_points": 16.2, "drafted": False, "source": "ESPN_Mock"},
        {"rank": "9", "name": "Davante Adams", "position": "WR", "team": "LV", "projected_points": 248.7, "avg_points": 15.6, "drafted": False, "source": "ESPN_Mock"},
        {"rank": "11", "name": "Stefon Diggs", "position": "WR", "team": "BUF", "projected_points": 242.1, "avg_points": 15.1, "drafted": False, "source": "ESPN_Mock"},
        {"rank": "13", "name": "CeeDee Lamb", "position": "WR", "team": "DAL", "projected_points": 238.5, "avg_points": 14.9, "drafted": False, "source": "ESPN_Mock"},
        {"rank": "15", "name": "A.J. Brown", "position": "WR", "team": "PHI", "projected_points": 232.8, "avg_points": 14.5, "drafted": False, "source": "ESPN_Mock"},
        
        # Top TEs
        {"rank": "14", "name": "Travis Kelce", "position": "TE", "team": "KC", "projected_points": 198.5, "avg_points": 12.4, "drafted": False, "source": "ESPN_Mock"},
        {"rank": "16", "name": "Mark Andrews", "position": "TE", "team": "BAL", "projected_points": 168.9, "avg_points": 10.6, "drafted": False, "source": "ESPN_Mock"},
        {"rank": "22", "name": "T.J. Hockenson", "position": "TE", "team": "MIN", "projected_points": 148.7, "avg_points": 9.3, "drafted": False, "source": "ESPN_Mock"},
        
        # Additional players for depth
        {"rank": "17", "name": "Nick Chubb", "position": "RB", "team": "CLE", "projected_points": 228.4, "avg_points": 14.3, "drafted": False, "source": "ESPN_Mock"},
        {"rank": "19", "name": "Ja'Marr Chase", "position": "WR", "team": "CIN", "projected_points": 225.6, "avg_points": 14.1, "drafted": False, "source": "ESPN_Mock"},
        {"rank": "20", "name": "Joe Burrow", "position": "QB", "team": "CIN", "projected_points": 268.2, "avg_points": 19.9, "drafted": False, "source": "ESPN_Mock"},
        {"rank": "21", "name": "Aaron Jones", "position": "RB", "team": "GB", "projected_points": 218.9, "avg_points": 13.7, "drafted": False, "source": "ESPN_Mock"},
        {"rank": "23", "name": "Mike Evans", "position": "WR", "team": "TB", "projected_points": 212.5, "avg_points": 13.3, "drafted": False, "source": "ESPN_Mock"},
        {"rank": "24", "name": "DeAndre Hopkins", "position": "WR", "team": "ARI", "projected_points": 208.7, "avg_points": 13.0, "drafted": False, "source": "ESPN_Mock"},
        {"rank": "25", "name": "Alvin Kamara", "position": "RB", "team": "NO", "projected_points": 205.3, "avg_points": 12.8, "drafted": False, "source": "ESPN_Mock"}
    ]

def populate_mock_espn_data():
    """Populate the database with comprehensive mock ESPN data"""
    print("Creating comprehensive mock ESPN data...")
    logger.info("Populating with mock ESPN data since no valid league credentials found")
    
    try:
        mock_players = create_comprehensive_mock_espn_data()
        logger.info(f"Inserting {len(mock_players)} mock ESPN players...")
        insert_players(mock_players)
        logger.info("Mock ESPN data insertion successful!")
        print(f"Successfully populated database with {len(mock_players)} mock ESPN players")
        return True
        
    except Exception as e:
        logger.error(f"Error inserting mock ESPN data: {e}")
        print(f"Failed to insert mock ESPN data: {e}")
        return False

def populate_from_real_espn():
    """Try to populate from real ESPN data if credentials are available"""
    from populate_espn import populate_from_espn
    
    espn_s2 = os.getenv("ESPN_S2")
    swid = os.getenv("SWID")
    
    if not espn_s2 or not swid:
        print("No ESPN_S2 and SWID found in environment variables")
        print("To use real ESPN data, add these to your .env file:")
        print("ESPN_S2=your_espn_s2_cookie_value")
        print("SWID=your_swid_cookie_value")
        print("")
        print("You can find these values in your browser cookies when logged into ESPN Fantasy")
        return False
    
    # Test with the user's private league
    test_league_id = '1004124703'
    print(f"Attempting to fetch real ESPN data from league {test_league_id}")
    
    try:
        populate_from_espn(test_league_id, year=2024)
        print("Real ESPN data population successful!")
        return True
    except Exception as e:
        print(f"Real ESPN population failed: {e}")
        return False

if __name__ == "__main__":
    print("ESPN Data Population Test")
    print("=" * 50)
    
    # Try real ESPN first if credentials are available
    print("Step 1: Trying real ESPN data...")
    real_espn_success = populate_from_real_espn()
    
    if not real_espn_success:
        print("\nStep 2: Falling back to mock ESPN data...")
        mock_success = populate_mock_espn_data()
        
        if mock_success:
            print("\n✅ Success! Your fantasy football draft assistant now has ESPN player data.")
            print("   You can use the web interface to search and filter players.")
            print("   To use real ESPN data later, add ESPN_S2 and SWID to your .env file.")
        else:
            print("\n❌ Failed to populate any ESPN data.")
    else:
        print("\n✅ Success! Real ESPN data has been populated.")
        
    print("\nTo test the web interface, run: python app.py")
