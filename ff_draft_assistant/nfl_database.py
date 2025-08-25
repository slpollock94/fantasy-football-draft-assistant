#!/usr/bin/env python3
"""
NFL Player Database Populator

This module fetches comprehensive NFL player data from multiple sources and 
provides advanced search functionality for the fantasy football draft assistant.
"""

import logging
import requests
import json
from typing import List, Dict, Any, Optional
from mongo_utils import insert_players

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NFLPlayerDatabase:
    """Comprehensive NFL player database manager"""
    
    def __init__(self):
        self.base_url = "https://api.sleeper.app/v1"
        self.players_cache = {}
        
    def fetch_all_nfl_players(self) -> Dict[str, Any]:
        """Fetch all NFL players from Sleeper API"""
        try:
            logger.info("Fetching comprehensive NFL player database from Sleeper API...")
            response = requests.get(f"{self.base_url}/players/nfl", timeout=30)
            response.raise_for_status()
            
            players_data = response.json()
            logger.info(f"Successfully fetched {len(players_data)} NFL players")
            self.players_cache = players_data
            return players_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch NFL players: {e}")
            return {}
    
    def get_fantasy_relevant_players(self, players_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter and format players for fantasy relevance"""
        fantasy_players = []
        
        # Positions we care about for fantasy
        fantasy_positions = ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']
        
        for player_id, player_info in players_data.items():
            try:
                # Skip players without essential info
                if not player_info.get('position') or not player_info.get('full_name'):
                    continue
                    
                position = player_info.get('position', '')
                if position not in fantasy_positions:
                    continue
                
                # Skip inactive/retired players where possible
                status = player_info.get('status', '').lower()
                if status in ['retired', 'suspended']:
                    continue
                
                # Create standardized player record
                player_record = {
                    'player_id': player_id,
                    'name': player_info.get('full_name', ''),
                    'position': position,
                    'team': player_info.get('team', ''),
                    'number': player_info.get('number'),
                    'age': player_info.get('age'),
                    'height': player_info.get('height', ''),
                    'weight': player_info.get('weight'),
                    'college': player_info.get('college', ''),
                    'years_exp': player_info.get('years_exp', 0),
                    'status': player_info.get('status', 'Active'),
                    'injury_status': player_info.get('injury_status', ''),
                    'projected_points': self._estimate_fantasy_points(player_info),
                    'avg_points': 0.0,  # Will be updated with actual data later
                    'drafted': False,
                    'source': 'NFL_Sleeper_API',
                    'rank': ''  # Will be calculated based on projections
                }
                
                fantasy_players.append(player_record)
                
            except Exception as e:
                logger.warning(f"Error processing player {player_id}: {e}")
                continue
        
        # Sort by estimated fantasy value and assign ranks
        fantasy_players.sort(key=lambda x: x['projected_points'], reverse=True)
        for i, player in enumerate(fantasy_players):
            player['rank'] = str(i + 1)
        
        logger.info(f"Processed {len(fantasy_players)} fantasy-relevant players")
        return fantasy_players
    
    def _estimate_fantasy_points(self, player_info: Dict[str, Any]) -> float:
        """Estimate fantasy points based on position and other factors"""
        position = player_info.get('position', '')
        years_exp = player_info.get('years_exp', 0)
        age = player_info.get('age', 25)
        
        # Base projections by position (rough estimates)
        base_projections = {
            'QB': 220.0,
            'RB': 180.0,
            'WR': 160.0,
            'TE': 120.0,
            'K': 100.0,
            'DEF': 90.0
        }
        
        base_points = base_projections.get(position, 50.0)
        
        # Adjust for experience (peak around 3-8 years)
        if years_exp >= 2 and years_exp <= 8:
            experience_modifier = 1.1
        elif years_exp > 8 or years_exp == 0:
            experience_modifier = 0.8
        else:
            experience_modifier = 0.9
        
        # Adjust for age (peak around 24-28)
        if age >= 24 and age <= 28:
            age_modifier = 1.0
        elif age > 28:
            age_modifier = max(0.7, 1.0 - (age - 28) * 0.05)
        else:
            age_modifier = 0.8
        
        estimated_points = base_points * experience_modifier * age_modifier
        
        # Add some randomization for variety
        import random
        estimated_points *= random.uniform(0.7, 1.3)
        
        return round(estimated_points, 1)
    
    def get_top_players_by_position(self, players: List[Dict[str, Any]], 
                                  position: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get top players for a specific position"""
        position_players = [p for p in players if p['position'] == position]
        position_players.sort(key=lambda x: x['projected_points'], reverse=True)
        return position_players[:limit]
    
    def populate_database(self, max_players: int = 1000) -> bool:
        """Populate the database with comprehensive NFL player data"""
        try:
            # Fetch all players
            all_players = self.fetch_all_nfl_players()
            if not all_players:
                logger.error("Failed to fetch player data")
                return False
            
            # Process and filter for fantasy relevance
            fantasy_players = self.get_fantasy_relevant_players(all_players)
            
            # Limit to specified number (top players by projected points)
            if len(fantasy_players) > max_players:
                fantasy_players = fantasy_players[:max_players]
                logger.info(f"Limited to top {max_players} players")
            
            # Insert into database
            logger.info(f"Inserting {len(fantasy_players)} players into database...")
            insert_players(fantasy_players)
            
            # Log summary by position
            position_counts = {}
            for player in fantasy_players:
                pos = player['position']
                position_counts[pos] = position_counts.get(pos, 0) + 1
            
            logger.info("Players added by position:")
            for pos, count in sorted(position_counts.items()):
                logger.info(f"  {pos}: {count} players")
            
            return True
            
        except Exception as e:
            logger.error(f"Error populating database: {e}")
            return False

def create_mock_comprehensive_database() -> List[Dict[str, Any]]:
    """Create a comprehensive mock NFL database for testing"""
    mock_players = []
    
    # Top QBs
    qb_data = [
        ("Josh Allen", "BUF", 28, 312.8), ("Lamar Jackson", "BAL", 27, 298.4),
        ("Patrick Mahomes", "KC", 29, 285.6), ("Jalen Hurts", "PHI", 25, 279.3),
        ("Dak Prescott", "DAL", 31, 265.8), ("Tua Tagovailoa", "MIA", 26, 258.9),
        ("Trevor Lawrence", "JAX", 25, 252.1), ("Joe Burrow", "CIN", 27, 248.7),
        ("Justin Herbert", "LAC", 26, 242.1), ("Kyler Murray", "ARI", 27, 238.5),
        ("Russell Wilson", "DEN", 36, 232.8), ("Aaron Rodgers", "NYJ", 41, 228.4),
        ("Geno Smith", "SEA", 34, 218.9), ("Derek Carr", "NO", 33, 212.5),
        ("Justin Fields", "CHI", 25, 208.7), ("Anthony Richardson", "IND", 22, 205.3),
        ("Brock Purdy", "SF", 24, 198.5), ("Jared Goff", "DET", 30, 195.8),
        ("Kirk Cousins", "ATL", 36, 188.9), ("Daniel Jones", "NYG", 27, 182.4)
    ]
    
    for i, (name, team, age, proj) in enumerate(qb_data):
        mock_players.append({
            'player_id': f'qb_{i+1}',
            'name': name, 'position': 'QB', 'team': team, 'age': age,
            'projected_points': proj, 'avg_points': round(proj * 0.7, 1),
            'drafted': False, 'source': 'NFL_Mock_Comprehensive',
            'rank': str(i + 1), 'years_exp': max(1, age - 22),
            'status': 'Active', 'injury_status': '', 'height': '6\'3"', 'weight': 225
        })
    
    # Top RBs
    rb_data = [
        ("Christian McCaffrey", "SF", 28, 285.6), ("Austin Ekeler", "LAC", 29, 268.9),
        ("Derrick Henry", "TEN", 30, 255.4), ("Jonathan Taylor", "IND", 25, 248.7),
        ("Saquon Barkley", "NYG", 27, 242.1), ("Nick Chubb", "CLE", 28, 238.5),
        ("Josh Jacobs", "LV", 26, 232.8), ("Aaron Jones", "GB", 29, 228.4),
        ("Alvin Kamara", "NO", 29, 225.6), ("Dalvin Cook", "FA", 29, 218.9),
        ("Joe Mixon", "CIN", 27, 215.3), ("Leonard Fournette", "FA", 29, 208.7),
        ("Ezekiel Elliott", "NE", 28, 205.3), ("Miles Sanders", "CAR", 27, 198.5),
        ("Kenneth Walker III", "SEA", 24, 195.8), ("Breece Hall", "NYJ", 23, 192.4),
        ("Javonte Williams", "DEN", 24, 188.9), ("David Montgomery", "DET", 27, 185.6),
        ("Tony Pollard", "DAL", 27, 182.4), ("J.K. Dobbins", "BAL", 25, 178.9),
        ("Cam Akers", "LAR", 25, 175.3), ("Antonio Gibson", "WAS", 26, 172.1),
        ("Dameon Pierce", "HOU", 24, 168.7), ("Isiah Pacheco", "KC", 25, 165.4),
        ("Rhamondre Stevenson", "NE", 26, 162.8), ("Travis Etienne", "JAX", 25, 159.6)
    ]
    
    for i, (name, team, age, proj) in enumerate(rb_data):
        mock_players.append({
            'player_id': f'rb_{i+1}',
            'name': name, 'position': 'RB', 'team': team, 'age': age,
            'projected_points': proj, 'avg_points': round(proj * 0.7, 1),
            'drafted': False, 'source': 'NFL_Mock_Comprehensive',
            'rank': str(len(mock_players) + 1), 'years_exp': max(1, age - 22),
            'status': 'Active', 'injury_status': '', 'height': '5\'11"', 'weight': 215
        })
    
    # Top WRs
    wr_data = [
        ("Cooper Kupp", "LAR", 31, 268.9), ("Davante Adams", "LV", 31, 255.4),
        ("Tyreek Hill", "MIA", 30, 248.7), ("Stefon Diggs", "BUF", 31, 242.1),
        ("DeAndre Hopkins", "ARI", 32, 238.5), ("Keenan Allen", "LAC", 32, 232.8),
        ("CeeDee Lamb", "DAL", 25, 228.4), ("A.J. Brown", "PHI", 27, 225.6),
        ("Mike Evans", "TB", 31, 218.9), ("Calvin Ridley", "JAX", 29, 215.3),
        ("DK Metcalf", "SEA", 27, 212.5), ("Amari Cooper", "CLE", 30, 208.7),
        ("Terry McLaurin", "WAS", 29, 205.3), ("Tyler Lockett", "SEA", 32, 198.5),
        ("Ja'Marr Chase", "CIN", 24, 195.8), ("Justin Jefferson", "MIN", 25, 192.4),
        ("Tee Higgins", "CIN", 25, 188.9), ("DJ Moore", "CHI", 27, 185.6),
        ("Chris Olave", "NO", 24, 182.4), ("Jaylen Waddle", "MIA", 25, 178.9),
        ("Amon-Ra St. Brown", "DET", 25, 175.3), ("Gabriel Davis", "BUF", 25, 172.1),
        ("Drake London", "ATL", 23, 168.7), ("Garrett Wilson", "NYJ", 24, 165.4),
        ("Courtland Sutton", "DEN", 29, 162.8), ("Michael Pittman Jr.", "IND", 27, 159.6),
        ("Brandon Aiyuk", "SF", 26, 156.8), ("Deebo Samuel", "SF", 28, 153.9),
        ("Allen Robinson", "PIT", 31, 148.7), ("JuJu Smith-Schuster", "KC", 28, 145.6)
    ]
    
    for i, (name, team, age, proj) in enumerate(wr_data):
        mock_players.append({
            'player_id': f'wr_{i+1}',
            'name': name, 'position': 'WR', 'team': team, 'age': age,
            'projected_points': proj, 'avg_points': round(proj * 0.7, 1),
            'drafted': False, 'source': 'NFL_Mock_Comprehensive',
            'rank': str(len(mock_players) + 1), 'years_exp': max(1, age - 22),
            'status': 'Active', 'injury_status': '', 'height': '6\'1"', 'weight': 200
        })
    
    # Top TEs
    te_data = [
        ("Travis Kelce", "KC", 35, 198.5), ("Mark Andrews", "BAL", 29, 185.6),
        ("George Kittle", "SF", 31, 172.8), ("T.J. Hockenson", "MIN", 27, 168.9),
        ("Darren Waller", "NYG", 32, 162.4), ("Kyle Pitts", "ATL", 24, 158.7),
        ("Dallas Goedert", "PHI", 29, 152.3), ("Pat Freiermuth", "PIT", 26, 148.9),
        ("David Njoku", "CLE", 28, 145.6), ("Tyler Higbee", "LAR", 31, 138.7),
        ("Gerald Everett", "LAC", 30, 135.4), ("Noah Fant", "SEA", 27, 132.1),
        ("Hunter Henry", "NE", 30, 128.9), ("Evan Engram", "JAX", 30, 125.6),
        ("Cole Kmet", "CHI", 25, 122.4), ("Dawson Knox", "BUF", 28, 118.7)
    ]
    
    for i, (name, team, age, proj) in enumerate(te_data):
        mock_players.append({
            'player_id': f'te_{i+1}',
            'name': name, 'position': 'TE', 'team': team, 'age': age,
            'projected_points': proj, 'avg_points': round(proj * 0.7, 1),
            'drafted': False, 'source': 'NFL_Mock_Comprehensive',
            'rank': str(len(mock_players) + 1), 'years_exp': max(1, age - 22),
            'status': 'Active', 'injury_status': '', 'height': '6\'4"', 'weight': 250
        })
    
    # Top Kickers
    k_data = [
        ("Justin Tucker", "BAL", 34, 145.6), ("Daniel Carlson", "LV", 29, 138.7),
        ("Tyler Bass", "BUF", 27, 135.4), ("Harrison Butker", "KC", 29, 132.1),
        ("Younghoe Koo", "ATL", 30, 128.9), ("Jake Elliott", "PHI", 29, 125.6),
        ("Brandon McManus", "JAX", 33, 122.4), ("Matt Gay", "IND", 30, 118.7),
        ("Ryan Succop", "TB", 38, 115.3), ("Robbie Gould", "SF", 42, 112.1)
    ]
    
    for i, (name, team, age, proj) in enumerate(k_data):
        mock_players.append({
            'player_id': f'k_{i+1}',
            'name': name, 'position': 'K', 'team': team, 'age': age,
            'projected_points': proj, 'avg_points': round(proj * 0.7, 1),
            'drafted': False, 'source': 'NFL_Mock_Comprehensive',
            'rank': str(len(mock_players) + 1), 'years_exp': max(1, age - 22),
            'status': 'Active', 'injury_status': '', 'height': '6\'0"', 'weight': 190
        })
    
    # Top Defenses
    def_data = [
        ("49ers", "SF", 125.6), ("Bills", "BUF", 122.4), ("Cowboys", "DAL", 118.7),
        ("Patriots", "NE", 115.3), ("Steelers", "PIT", 112.1), ("Ravens", "BAL", 108.9),
        ("Broncos", "DEN", 105.6), ("Saints", "NO", 102.4), ("Jets", "NYJ", 98.7),
        ("Eagles", "PHI", 95.3), ("Chargers", "LAC", 92.1), ("Browns", "CLE", 88.9)
    ]
    
    for i, (name, team, proj) in enumerate(def_data):
        mock_players.append({
            'player_id': f'def_{i+1}',
            'name': f"{name} Defense", 'position': 'DEF', 'team': team, 'age': 0,
            'projected_points': proj, 'avg_points': round(proj * 0.7, 1),
            'drafted': False, 'source': 'NFL_Mock_Comprehensive',
            'rank': str(len(mock_players) + 1), 'years_exp': 0,
            'status': 'Active', 'injury_status': '', 'height': '', 'weight': 0
        })
    
    return mock_players

def main():
    """Main function to populate NFL database"""
    print("NFL Player Database Populator")
    print("=" * 50)
    
    db = NFLPlayerDatabase()
    
    print("Option 1: Fetching real NFL data from Sleeper API...")
    success = db.populate_database(max_players=500)
    
    if not success:
        print("\nOption 2: Using comprehensive mock NFL database...")
        try:
            mock_players = create_mock_comprehensive_database()
            logger.info(f"Inserting {len(mock_players)} comprehensive mock players...")
            insert_players(mock_players)
            
            # Summary
            position_counts = {}
            for player in mock_players:
                pos = player['position']
                position_counts[pos] = position_counts.get(pos, 0) + 1
            
            print(f"\n✅ Successfully populated database with {len(mock_players)} NFL players!")
            print("\nPlayers by position:")
            for pos, count in sorted(position_counts.items()):
                print(f"  {pos}: {count} players")
                
            success = True
            
        except Exception as e:
            logger.error(f"Failed to populate mock database: {e}")
            success = False
    
    if success:
        print(f"\n🏈 NFL database population complete!")
        print("You can now use the enhanced search functionality.")
    else:
        print(f"\n❌ Failed to populate NFL database.")

if __name__ == "__main__":
    main()
