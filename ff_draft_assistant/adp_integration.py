import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)

class ADPDataSource:
    """Integration with Fantasy Football Calculator and other ADP sources"""
    
    def __init__(self):
        self.base_url = "https://fantasyfootballcalculator.com/api/v1/adp"
        self.cache_duration = timedelta(hours=6)  # Cache for 6 hours
        self.cache_file = "adp_cache.json"
        
        # Backup ADP sources (if primary fails)
        self.backup_sources = [
            "https://www.fantasypros.com/nfl/adp/",  # Requires scraping
            # Add more sources as needed
        ]
    
    def get_adp_data(self, format_type='ppr', teams=12, year=None) -> Optional[List[Dict]]:
        """Fetch ADP data from Fantasy Football Calculator
        
        Args:
            format_type: 'ppr', 'standard', 'half-ppr', '2qb', 'dynasty'
            teams: League size (8, 10, 12, 14, 16)
            year: Year for historical data (defaults to current year)
        """
        if year is None:
            year = datetime.now().year
        
        # Check cache first
        cached_data = self._get_cached_data(format_type, teams, year)
        if cached_data:
            logger.info(f"Using cached ADP data for {format_type}")
            return cached_data
        
        url = f"{self.base_url}/{format_type}"
        params = {'teams': teams, 'year': year}
        
        try:
            logger.info(f"Fetching ADP data from {url} with params {params}")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Process and standardize the data
            processed_data = self._process_ffc_data(data, format_type)
            
            # Cache the results
            self._cache_data(processed_data, format_type, teams, year)
            
            logger.info(f"Successfully fetched {len(processed_data)} ADP entries")
            return processed_data
            
        except requests.RequestException as e:
            logger.error(f"Error fetching ADP data from FFC: {e}")
            return self._get_backup_adp_data(format_type, teams, year)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from FFC: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching ADP data: {e}")
            return None
    
    def get_multi_format_adp(self, teams=12, year=None) -> Dict[str, List[Dict]]:
        """Get ADP data from multiple formats for consensus calculation"""
        formats = ['standard', 'ppr', 'half-ppr']
        all_adp = {}
        
        for format_type in formats:
            data = self.get_adp_data(format_type, teams, year)
            if data:
                all_adp[format_type] = data
                logger.info(f"Retrieved {len(data)} players for {format_type}")
        
        return all_adp
    
    def calculate_consensus_adp(self, multi_format_data: Dict[str, List[Dict]]) -> List[Dict]:
        """Calculate consensus ADP from multiple formats"""
        if not multi_format_data:
            return []
        
        # Create player mapping across formats
        player_adp = {}
        
        for format_type, players in multi_format_data.items():
            for player in players:
                player_key = self._create_player_key(player)
                
                if player_key not in player_adp:
                    player_adp[player_key] = {
                        'name': player['name'],
                        'position': player['position'],
                        'team': player.get('team', ''),
                        'adp_data': {},
                        'consensus_adp': 0,
                        'formats_count': 0
                    }
                
                player_adp[player_key]['adp_data'][format_type] = player['adp']
                player_adp[player_key]['formats_count'] += 1
        
        # Calculate consensus ADP (average across formats)
        consensus_players = []
        for player_key, player_data in player_adp.items():
            adp_values = list(player_data['adp_data'].values())
            if adp_values:
                player_data['consensus_adp'] = round(sum(adp_values) / len(adp_values), 1)
                consensus_players.append(player_data)
        
        # Sort by consensus ADP
        consensus_players.sort(key=lambda x: x['consensus_adp'])
        
        logger.info(f"Generated consensus ADP for {len(consensus_players)} players")
        return consensus_players
    
    def merge_adp_with_players(self, players: List[Dict], adp_data: List[Dict]) -> List[Dict]:
        """Merge ADP data into existing player records"""
        # Create ADP lookup dictionary
        adp_lookup = {}
        for adp_player in adp_data:
            key = self._create_player_key(adp_player)
            adp_lookup[key] = adp_player
        
        # Merge ADP data into players
        updated_players = []
        matched_count = 0
        
        for player in players:
            player_copy = player.copy()
            key = self._create_player_key(player)
            
            if key in adp_lookup:
                adp_info = adp_lookup[key]
                player_copy['adp'] = adp_info.get('consensus_adp', adp_info.get('adp'))
                player_copy['adp_data'] = adp_info.get('adp_data', {})
                matched_count += 1
            
            updated_players.append(player_copy)
        
        logger.info(f"Merged ADP data for {matched_count}/{len(players)} players")
        return updated_players
    
    def _process_ffc_data(self, raw_data: Dict, format_type: str) -> List[Dict]:
        """Process raw Fantasy Football Calculator data"""
        processed = []
        
        # Handle different response formats
        players_data = raw_data.get('players', raw_data)
        
        if isinstance(players_data, list):
            for item in players_data:
                processed_player = self._process_ffc_player(item, format_type)
                if processed_player:
                    processed.append(processed_player)
        elif isinstance(players_data, dict):
            for player_data in players_data.values():
                processed_player = self._process_ffc_player(player_data, format_type)
                if processed_player:
                    processed.append(processed_player)
        
        return processed
    
    def _process_ffc_player(self, player_data: Dict, format_type: str) -> Optional[Dict]:
        """Process individual player data from FFC"""
        try:
            # Handle different data structures
            name = player_data.get('name', player_data.get('player_name', ''))
            position = player_data.get('position', player_data.get('pos', ''))
            team = player_data.get('team', player_data.get('team_abbr', ''))
            adp = player_data.get('adp', player_data.get('avg_pick', 0))
            
            if not name or not position:
                return None
            
            return {
                'name': name.strip(),
                'position': position.upper(),
                'team': team.upper() if team else '',
                'adp': float(adp) if adp else None,
                'format': format_type,
                'source': 'fantasyfootballcalculator'
            }
            
        except Exception as e:
            logger.warning(f"Error processing player data: {e}")
            return None
    
    def _create_player_key(self, player: Dict) -> str:
        """Create a consistent key for player matching"""
        name = player.get('name', '').strip().lower()
        position = player.get('position', '').upper()
        team = player.get('team', '').upper()
        
        # Normalize name for better matching
        name = name.replace('.', '').replace("'", '').replace('-', ' ')
        name = ' '.join(name.split())
        
        return f"{name}_{position}_{team}"
    
    def _get_cached_data(self, format_type: str, teams: int, year: int) -> Optional[List[Dict]]:
        """Retrieve cached ADP data if still valid"""
        if not os.path.exists(self.cache_file):
            return None
        
        try:
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
            
            cache_key = f"{format_type}_{teams}_{year}"
            
            if cache_key in cache:
                cached_entry = cache[cache_key]
                cache_time = datetime.fromisoformat(cached_entry['timestamp'])
                
                if datetime.now() - cache_time < self.cache_duration:
                    return cached_entry['data']
        
        except Exception as e:
            logger.warning(f"Error reading ADP cache: {e}")
        
        return None
    
    def _cache_data(self, data: List[Dict], format_type: str, teams: int, year: int):
        """Cache ADP data for future use"""
        try:
            cache = {}
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
            
            cache_key = f"{format_type}_{teams}_{year}"
            cache[cache_key] = {
                'data': data,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache, f, indent=2)
            
            logger.debug(f"Cached ADP data for {cache_key}")
            
        except Exception as e:
            logger.warning(f"Error caching ADP data: {e}")
    
    def _get_backup_adp_data(self, format_type: str, teams: int, year: int) -> Optional[List[Dict]]:
        """Fallback to backup ADP sources or mock data"""
        logger.info("Attempting backup ADP sources...")
        
        # For now, return None - could implement FantasyPros scraping or other sources
        # In a real implementation, you might scrape other sites or use mock data
        return None
    
    def get_player_adp_history(self, player_name: str, position: str, years: List[int] = None) -> Dict:
        """Get historical ADP data for a specific player"""
        if years is None:
            current_year = datetime.now().year
            years = [current_year - 1, current_year]
        
        history = {}
        
        for year in years:
            for format_type in ['standard', 'ppr']:
                data = self.get_adp_data(format_type, year=year)
                if data:
                    for player in data:
                        if (player['name'].lower() == player_name.lower() and 
                            player['position'] == position.upper()):
                            
                            if year not in history:
                                history[year] = {}
                            history[year][format_type] = player['adp']
                            break
        
        return history