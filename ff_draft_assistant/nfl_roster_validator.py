import requests
import logging
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)

class NFLRosterValidator:
    """Enhanced NFL roster validation using multiple data sources"""
    
    def __init__(self):
        self.cache_file = "nfl_roster_cache.json"
        self.cache_duration = timedelta(hours=24)  # Cache for 24 hours
        
        # NFL data sources (free APIs)
        self.data_sources = [
            {
                'name': 'sleeper',
                'url': 'https://api.sleeper.app/v1/players/nfl',
                'parser': self._parse_sleeper_data
            },
            {
                'name': 'nfl_data_py_backup', 
                'url': 'https://github.com/nflverse/nfldata/releases/latest/download/players.json',
                'parser': self._parse_nfldata_format
            }
        ]
        
        # Current NFL teams with depth chart priority positions
        self.nfl_team_depth_positions = {
            'QB': 3,   # Teams typically keep 2-3 QBs
            'RB': 4,   # Teams keep 3-4 RBs
            'WR': 6,   # Teams keep 5-6 WRs
            'TE': 3,   # Teams keep 2-3 TEs
            'K': 1,    # Teams keep 1 K
            'DEF': 1   # Teams keep 1 DEF unit
        }
        
        # Active NFL roster data
        self.active_players = set()
        self.player_details = {}
        
    def get_active_nfl_players(self) -> Set[str]:
        """Get set of active NFL player keys"""
        # Try cache first
        cached_data = self._load_cached_roster()
        if cached_data:
            logger.info("Using cached NFL roster data")
            return cached_data
        
        # Fetch fresh data
        logger.info("Fetching fresh NFL roster data...")
        active_players = set()
        
        for source in self.data_sources:
            try:
                players = self._fetch_from_source(source)
                if players:
                    active_players.update(players)
                    logger.info(f"Retrieved {len(players)} players from {source['name']}")
                    break  # Use first successful source
            except Exception as e:
                logger.warning(f"Failed to fetch from {source['name']}: {e}")
                continue
        
        if active_players:
            self._cache_roster_data(active_players)
            self.active_players = active_players
            return active_players
        
        logger.error("Failed to retrieve NFL roster data from all sources")
        return set()
    
    def _fetch_from_source(self, source: Dict) -> Optional[Set[str]]:
        """Fetch player data from a specific source"""
        try:
            response = requests.get(source['url'], timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return source['parser'](data)
            
        except Exception as e:
            logger.error(f"Error fetching from {source['name']}: {e}")
            return None
    
    def _parse_sleeper_data(self, data: Dict) -> Set[str]:
        """Parse Sleeper API player data"""
        active_players = set()
        player_details = {}
        
        for player_id, player_info in data.items():
            if not isinstance(player_info, dict):
                continue
                
            # Check if player is active
            status = player_info.get('status', '').upper()
            if status in ['RETIRED', 'SUSPENDED', 'INACTIVE']:
                continue
            
            # Must have valid team and position
            team = player_info.get('team')
            position = player_info.get('position')
            name = player_info.get('full_name') or f"{player_info.get('first_name', '')} {player_info.get('last_name', '')}".strip()
            
            if not team or not position or not name or team.upper() in ['NONE', 'NULL', '']:
                continue
            
            # Filter by fantasy relevance and roster likelihood
            if not self._is_likely_rostered(player_info):
                continue
            
            player_key = self._create_player_key(name, position, team)
            active_players.add(player_key)
            
            # Store detailed info
            player_details[player_key] = {
                'name': name,
                'position': position,
                'team': team,
                'status': status,
                'years_exp': player_info.get('years_exp', 0),
                'age': player_info.get('age'),
                'height': player_info.get('height'),
                'weight': player_info.get('weight'),
                'college': player_info.get('college'),
                'sleeper_id': player_id
            }
        
        self.player_details = player_details
        logger.info(f"Parsed {len(active_players)} active NFL players from Sleeper")
        return active_players
    
    def _parse_nfldata_format(self, data: List[Dict]) -> Set[str]:
        """Parse NFL data format (backup source)"""
        active_players = set()
        current_year = datetime.now().year
        
        for player in data:
            if not isinstance(player, dict):
                continue
            
            # Check if player is current/recent
            last_season = player.get('last_season', 0)
            if last_season < current_year - 1:  # Not active in last 2 years
                continue
            
            name = player.get('display_name') or player.get('full_name', '')
            position = player.get('position')
            team = player.get('team')
            
            if not all([name, position, team]):
                continue
            
            player_key = self._create_player_key(name, position, team)
            active_players.add(player_key)
        
        logger.info(f"Parsed {len(active_players)} active players from NFL data backup")
        return active_players
    
    def _is_likely_rostered(self, player_info: Dict) -> bool:
        """Determine if player is likely to be on an NFL roster"""
        position = player_info.get('position', '')
        team = player_info.get('team', '')
        years_exp = player_info.get('years_exp', 0)
        
        # Must have team
        if not team:
            return False
        
        # Position must be fantasy relevant
        if position not in self.nfl_team_depth_positions:
            return False
        
        # Players with 0 years experience might be practice squad
        # Include them if they have recent activity
        if years_exp == 0:
            # Check for rookie indicators
            stats_keys = ['rec_tds', 'rush_tds', 'pass_tds', 'fgm', 'rec', 'rush_att', 'pass_att']
            has_stats = any(player_info.get(key, 0) > 0 for key in stats_keys)
            return has_stats
        
        return True
    
    def _create_player_key(self, name: str, position: str, team: str) -> str:
        """Create consistent player key for matching"""
        # Normalize name
        clean_name = name.lower().strip()
        clean_name = clean_name.replace('.', '').replace("'", '').replace('-', ' ')
        clean_name = ' '.join(clean_name.split())
        
        return f"{clean_name}_{position.upper()}_{team.upper()}"
    
    def validate_player(self, player: Dict) -> bool:
        """Validate if player is active NFL player"""
        if not self.active_players:
            self.get_active_nfl_players()
        
        name = player.get('name', '')
        position = player.get('position', '')
        team = player.get('team', '')
        
        if not all([name, position, team]):
            return False
        
        # Skip if no team (free agents, retired players)
        if team in ['FA', 'None', '', None]:
            return False
        
        player_key = self._create_player_key(name, position, team)
        is_active = player_key in self.active_players
        
        if not is_active:
            # Try fuzzy matching for name variations
            is_active = self._fuzzy_match_player(name, position, team)
        
        return is_active
    
    def _fuzzy_match_player(self, name: str, position: str, team: str) -> bool:
        """Attempt fuzzy matching for player names"""
        from difflib import SequenceMatcher
        
        clean_name = name.lower().replace('.', '').replace("'", '').replace('-', ' ')
        clean_name = ' '.join(clean_name.split())
        
        # Look for similar names in same position and team
        for player_key in self.active_players:
            key_parts = player_key.split('_')
            if len(key_parts) >= 3:
                key_name = key_parts[0]
                key_position = key_parts[1]
                key_team = key_parts[2]
                
                if key_position == position.upper() and key_team == team.upper():
                    similarity = SequenceMatcher(None, clean_name, key_name).ratio()
                    if similarity > 0.85:  # 85% similarity threshold
                        logger.debug(f"Fuzzy matched: {name} -> {key_name} (similarity: {similarity:.2f})")
                        return True
        
        return False
    
    def get_player_details(self, name: str, position: str, team: str) -> Optional[Dict]:
        """Get detailed information about a specific player"""
        player_key = self._create_player_key(name, position, team)
        return self.player_details.get(player_key)
    
    def _load_cached_roster(self) -> Optional[Set[str]]:
        """Load cached roster data if still valid"""
        if not os.path.exists(self.cache_file):
            return None
        
        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cache_time < self.cache_duration:
                return set(cache_data['active_players'])
        
        except Exception as e:
            logger.warning(f"Error reading roster cache: {e}")
        
        return None
    
    def _cache_roster_data(self, active_players: Set[str]):
        """Cache roster data for future use"""
        try:
            cache_data = {
                'active_players': list(active_players),
                'timestamp': datetime.now().isoformat(),
                'count': len(active_players)
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.info(f"Cached {len(active_players)} active NFL players")
            
        except Exception as e:
            logger.warning(f"Error caching roster data: {e}")
    
    def get_validation_report(self, players: List[Dict]) -> Dict:
        """Generate validation report for a list of players"""
        if not self.active_players:
            self.get_active_nfl_players()
        
        total_players = len(players)
        valid_players = 0
        invalid_players = []
        team_issues = []
        
        for player in players:
            if self.validate_player(player):
                valid_players += 1
            else:
                invalid_players.append(player)
                
                # Track team issues
                team = player.get('team', 'Unknown')
                if team in ['FA', 'None', '', None]:
                    team_issues.append(f"{player.get('name', 'Unknown')} - No team")
        
        return {
            'total_players': total_players,
            'valid_players': valid_players,
            'invalid_players': len(invalid_players),
            'validation_rate': (valid_players / total_players * 100) if total_players > 0 else 0,
            'sample_invalid': invalid_players[:10],  # Show first 10 invalid players
            'team_issues': team_issues[:10],
            'active_nfl_count': len(self.active_players)
        }