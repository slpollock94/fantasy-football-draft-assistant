import re
import logging
from typing import List, Dict, Optional
from difflib import SequenceMatcher
from nfl_roster_validator import NFLRosterValidator

logger = logging.getLogger(__name__)

class PlayerDataValidator:
    """Enhanced player data validation and cleaning for NFL fantasy football"""
    
    def __init__(self):
        self.nfl_teams = {
            'ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE',
            'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC',
            'LV', 'LAC', 'LAR', 'MIA', 'MIN', 'NE', 'NO', 'NYG',
            'NYJ', 'PHI', 'PIT', 'SF', 'SEA', 'TB', 'TEN', 'WAS'
        }
        
        # Initialize NFL roster validator for active player checking
        self.roster_validator = NFLRosterValidator()
        
        self.fantasy_positions = {'QB', 'RB', 'WR', 'TE', 'K', 'DEF', 'DST'}
        
        # Common name variations mapping
        self.name_variations = {
            'DJ': 'D.J.',
            'AJ': 'A.J.',
            'TJ': 'T.J.',
            'CJ': 'C.J.',
            'JJ': 'J.J.',
            'RJ': 'R.J.',
            'BJ': 'B.J.',
            'MJ': 'M.J.',
            'PJ': 'P.J.'
        }
        
        # Team name mappings (common variations)
        self.team_mappings = {
            'LAS': 'LV',
            'LVRD': 'LV', 
            'WSH': 'WAS',
            'WFT': 'WAS',
            'JAC': 'JAX'
        }
    
    def clean_player_name(self, name: str) -> str:
        """Standardize player names"""
        if not name:
            return ""
        
        # Basic cleaning
        name = ' '.join(name.split())
        name = name.title()
        
        # Handle suffixes consistently
        name = re.sub(r'\s+(Jr\.?|Sr\.?|III|IV|V)$', '', name, flags=re.IGNORECASE)
        
        # Apply common variations
        for variant, standard in self.name_variations.items():
            name = re.sub(rf'\b{variant}\b', standard, name)
        
        # Remove non-alphabetic characters except spaces, periods, and apostrophes
        name = re.sub(r"[^a-zA-Z\s\.']+", '', name)
        
        return name.strip()
    
    def normalize_team(self, team: str) -> str:
        """Normalize team abbreviations"""
        if not team:
            return "FA"
        
        team = team.upper().strip()
        return self.team_mappings.get(team, team)
    
    def normalize_position(self, position: str) -> str:
        """Normalize position abbreviations"""
        if not position:
            return ""
        
        position = position.upper().strip()
        
        # Handle common variations
        position_mappings = {
            'D/ST': 'DEF',
            'DST': 'DEF',
            'FLEX': '',  # Remove flex designations
            'SUPERFLEX': '',
            'BN': '',  # Remove bench designations
        }
        
        return position_mappings.get(position, position)
    
    def validate_player_data(self, player: Dict) -> bool:
        """Validate individual player data with enhanced NFL roster checking"""
        # Required fields
        required_fields = ['name', 'position', 'team']
        if not all(field in player and player[field] for field in required_fields):
            return False
        
        # Clean and normalize data
        clean_name = self.clean_player_name(player['name'])
        if len(clean_name) < 2:
            return False
        
        # Valid position
        position = self.normalize_position(player['position'])
        if position not in self.fantasy_positions:
            return False
        
        # Valid team
        team = self.normalize_team(player['team'])
        if team not in self.nfl_teams:
            return False
        
        # Update player data with cleaned values
        player['name'] = clean_name
        player['position'] = position
        player['team'] = team
        
        # ENHANCED: Check if player is actually on active NFL roster
        is_active_nfl = self.roster_validator.validate_player(player)
        if not is_active_nfl:
            logger.debug(f"Player {clean_name} ({position} - {team}) not found on active NFL roster")
            return False
        
        return True
    
    def detect_duplicates(self, players: List[Dict]) -> List[Dict]:
        """Detect and merge duplicate player entries"""
        unique_players = []
        seen_players = {}
        
        for player in players:
            if not self.validate_player_data(player):
                continue
            
            clean_name = player['name']
            key = f"{clean_name}_{player['position']}_{player['team']}"
            
            # Check for exact matches
            if key in seen_players:
                # Merge data, keeping better information
                seen_players[key] = self._merge_player_data(seen_players[key], player)
                continue
            
            # Check for similar names (fuzzy matching)
            similar_found = False
            for existing_key, existing_player in seen_players.items():
                if (player['position'] == existing_player['position'] and 
                    player['team'] == existing_player['team']):
                    
                    similarity = SequenceMatcher(None, clean_name, existing_player['name']).ratio()
                    
                    if similarity > 0.9:  # 90% similarity threshold
                        seen_players[existing_key] = self._merge_player_data(existing_player, player)
                        similar_found = True
                        break
            
            if not similar_found:
                seen_players[key] = player.copy()
        
        return list(seen_players.values())
    
    def _merge_player_data(self, player1: Dict, player2: Dict) -> Dict:
        """Merge two player records, keeping the best information"""
        merged = player1.copy()
        
        # Prefer non-empty values and longer descriptions
        for key, value in player2.items():
            if value is not None and value != '':
                if key not in merged or not merged[key] or \
                   (isinstance(value, str) and len(str(value)) > len(str(merged.get(key, '')))):
                    merged[key] = value
                elif isinstance(value, (int, float)) and value > merged.get(key, 0):
                    merged[key] = value
        
        return merged
    
    def clean_database_players(self, players: List[Dict]) -> List[Dict]:
        """Clean and validate a list of players"""
        logger.info(f"Starting validation of {len(players)} players")
        
        # Remove duplicates and validate
        valid_players = self.detect_duplicates(players)
        
        # Additional filtering for fantasy relevance
        fantasy_relevant = []
        for player in valid_players:
            # Skip players without meaningful data
            if self._is_fantasy_relevant(player):
                fantasy_relevant.append(player)
        
        logger.info(f"Validation complete: {len(fantasy_relevant)} valid players from {len(players)} original")
        
        return fantasy_relevant
    
    def _is_fantasy_relevant(self, player: Dict) -> bool:
        """Check if player is relevant for fantasy football"""
        # Must have basic fantasy data
        if not player.get('name') or not player.get('position') or not player.get('team'):
            return False
        
        # Skip inactive/retired players if status is available
        status = player.get('status', '').upper()
        if status in ['RETIRED', 'SUSPENDED', 'INACTIVE']:
            return False
        
        # For skill positions, prefer players with some statistical data
        if player['position'] in ['QB', 'RB', 'WR', 'TE']:
            # If we have stats data, use it for relevance
            if any(key in player for key in ['projected_points', 'fantasy_points', 'adp', 'rank']):
                return True
            
            # Otherwise, include all active players
            return player.get('active', True)
        
        # Include all K and DEF positions
        return True
    
    def generate_validation_report(self, original_players: List[Dict], cleaned_players: List[Dict]) -> Dict:
        """Generate a report on data cleaning results"""
        original_count = len(original_players)
        cleaned_count = len(cleaned_players)
        
        # Count by position
        original_positions = {}
        cleaned_positions = {}
        
        for player in original_players:
            pos = player.get('position', 'UNKNOWN')
            original_positions[pos] = original_positions.get(pos, 0) + 1
        
        for player in cleaned_players:
            pos = player.get('position', 'UNKNOWN')
            cleaned_positions[pos] = cleaned_positions.get(pos, 0) + 1
        
        report = {
            'summary': {
                'original_count': original_count,
                'cleaned_count': cleaned_count,
                'removed_count': original_count - cleaned_count,
                'removal_percentage': round(((original_count - cleaned_count) / original_count * 100), 2) if original_count > 0 else 0
            },
            'positions': {
                'original': original_positions,
                'cleaned': cleaned_positions
            }
        }
        
        return report