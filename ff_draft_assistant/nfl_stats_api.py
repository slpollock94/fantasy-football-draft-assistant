import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)

class NFLStatsAPI:
    """NFL Statistics API integration for player historical data"""
    
    def __init__(self):
        self.cache_duration = timedelta(hours=12)
        self.stats_cache_dir = "stats_cache"
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(self.stats_cache_dir):
            os.makedirs(self.stats_cache_dir)
        
        # Free NFL stats APIs
        self.apis = {
            'sleeper': {
                'base_url': 'https://api.sleeper.app/v1',
                'endpoints': {
                    'players': '/players/nfl',
                    'stats': '/stats/nfl/regular/{year}'
                }
            },
            'nfl_data': {
                'base_url': 'https://github.com/nflverse/nfldata/releases/latest/download',
                'endpoints': {
                    'player_stats': '/player_stats.parquet',
                    'weekly_stats': '/play_by_play_{year}.parquet'
                }
            }
        }
    
    def get_player_career_stats(self, player_name: str, position: str, years: Optional[List[int]] = None) -> Dict:
        """Get career statistics for a player"""
        if years is None:
            current_year = datetime.now().year
            years = list(range(2020, current_year + 1))  # Last 4-5 seasons
        
        cache_key = f"{player_name}_{position}_career"
        cached_stats = self._load_cached_stats(cache_key)
        
        if cached_stats:
            logger.debug(f"Using cached stats for {player_name}")
            return cached_stats
        
        # Fetch fresh stats
        career_stats = {
            'player_name': player_name,
            'position': position,
            'seasons': {},
            'career_totals': {},
            'averages': {}
        }
        
        try:
            # Get player data from Sleeper first for ID mapping
            sleeper_data = self._get_sleeper_player_data()
            player_id = self._find_player_id(player_name, position, sleeper_data)
            
            if not player_id:
                logger.warning(f"Could not find player ID for {player_name}")
                return career_stats
            
            # Get stats for each year
            for year in years:
                year_stats = self._get_year_stats(player_id, year, position)
                if year_stats:
                    career_stats['seasons'][year] = year_stats
            
            # Calculate career totals and averages
            career_stats['career_totals'] = self._calculate_career_totals(career_stats['seasons'], position)
            career_stats['averages'] = self._calculate_averages(career_stats['seasons'], position)
            
            # Cache the results
            self._cache_stats(cache_key, career_stats)
            
            logger.info(f"Retrieved career stats for {player_name}")
            return career_stats
            
        except Exception as e:
            logger.error(f"Error fetching career stats for {player_name}: {e}")
            return career_stats
    
    def get_player_projections(self, player_name: str, position: str, year: Optional[int] = None) -> Dict:
        """Get player projections for the current/specified year"""
        if year is None:
            year = datetime.now().year
        
        cache_key = f"{player_name}_{position}_proj_{year}"
        cached_proj = self._load_cached_stats(cache_key)
        
        if cached_proj:
            return cached_proj
        
        # For now, generate basic projections based on historical data
        # In a real implementation, you'd integrate with fantasy projection APIs
        career_stats = self.get_player_career_stats(player_name, position)
        
        if not career_stats.get('averages'):
            return {}
        
        projections = {
            'player_name': player_name,
            'position': position,
            'year': year,
            'projected_stats': self._generate_basic_projections(career_stats['averages'], position),
            'confidence': 'Medium',  # Basic confidence level
            'last_updated': datetime.now().isoformat()
        }
        
        self._cache_stats(cache_key, projections)
        return projections
    
    def _get_sleeper_player_data(self) -> Dict:
        """Get all player data from Sleeper API"""
        try:
            response = requests.get(f"{self.apis['sleeper']['base_url']}/players/nfl", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching Sleeper player data: {e}")
            return {}
    
    def _find_player_id(self, player_name: str, position: str, sleeper_data: Dict) -> Optional[str]:
        """Find player ID from Sleeper data"""
        normalized_name = player_name.lower().replace('.', '').replace("'", '')
        
        for player_id, player_info in sleeper_data.items():
            if not isinstance(player_info, dict):
                continue
            
            # Check full name
            full_name = player_info.get('full_name', '').lower().replace('.', '').replace("'", '')
            if full_name == normalized_name and player_info.get('position') == position:
                return player_id
            
            # Check first + last name combination
            first_name = player_info.get('first_name', '').lower()
            last_name = player_info.get('last_name', '').lower()
            combined_name = f"{first_name} {last_name}".replace('.', '').replace("'", '')
            
            if combined_name == normalized_name and player_info.get('position') == position:
                return player_id
        
        return None
    
    def _get_year_stats(self, player_id: str, year: int, position: str) -> Dict:
        """Get stats for a specific year"""
        try:
            # Try Sleeper stats endpoint
            stats_url = f"{self.apis['sleeper']['base_url']}/stats/nfl/regular/{year}"
            response = requests.get(stats_url, timeout=10)
            
            if response.status_code == 200:
                all_stats = response.json()
                player_stats = all_stats.get(player_id, {})
                
                if player_stats:
                    return self._normalize_stats(player_stats, position, year)
            
        except Exception as e:
            logger.debug(f"Error fetching {year} stats for player {player_id}: {e}")
        
        return {}
    
    def _normalize_stats(self, raw_stats: Dict, position: str, year: int) -> Dict:
        """Normalize stats across different data sources"""
        normalized = {
            'year': year,
            'games_played': raw_stats.get('gp', 0)
        }
        
        if position == 'QB':
            normalized.update({
                'passing_yards': raw_stats.get('pass_yd', 0),
                'passing_tds': raw_stats.get('pass_td', 0),
                'interceptions': raw_stats.get('pass_int', 0),
                'rushing_yards': raw_stats.get('rush_yd', 0),
                'rushing_tds': raw_stats.get('rush_td', 0),
                'fantasy_points': raw_stats.get('pts_ppr', 0)
            })
        elif position == 'RB':
            normalized.update({
                'rushing_yards': raw_stats.get('rush_yd', 0),
                'rushing_tds': raw_stats.get('rush_td', 0),
                'receptions': raw_stats.get('rec', 0),
                'receiving_yards': raw_stats.get('rec_yd', 0),
                'receiving_tds': raw_stats.get('rec_td', 0),
                'fantasy_points': raw_stats.get('pts_ppr', 0)
            })
        elif position in ['WR', 'TE']:
            normalized.update({
                'receptions': raw_stats.get('rec', 0),
                'receiving_yards': raw_stats.get('rec_yd', 0),
                'receiving_tds': raw_stats.get('rec_td', 0),
                'rushing_yards': raw_stats.get('rush_yd', 0),
                'rushing_tds': raw_stats.get('rush_td', 0),
                'fantasy_points': raw_stats.get('pts_ppr', 0)
            })
        elif position == 'K':
            normalized.update({
                'field_goals_made': raw_stats.get('fgm', 0),
                'field_goals_attempted': raw_stats.get('fga', 0),
                'extra_points_made': raw_stats.get('xpm', 0),
                'fantasy_points': raw_stats.get('pts_std', 0)
            })
        
        return normalized
    
    def _calculate_career_totals(self, seasons: Dict, position: str) -> Dict:
        """Calculate career total statistics"""
        totals = {}
        
        for year_stats in seasons.values():
            for stat, value in year_stats.items():
                if stat != 'year' and isinstance(value, (int, float)):
                    totals[stat] = totals.get(stat, 0) + value
        
        return totals
    
    def _calculate_averages(self, seasons: Dict, position: str) -> Dict:
        """Calculate per-game and per-season averages"""
        if not seasons:
            return {}
        
        # Per-season averages
        per_season = {}
        total_games = 0
        games_played_seasons = 0
        
        for year_stats in seasons.values():
            games = year_stats.get('games_played', 0)
            if games > 0:
                total_games += games
                games_played_seasons += 1
            
            for stat, value in year_stats.items():
                if stat not in ['year', 'games_played'] and isinstance(value, (int, float)):
                    per_season[f"{stat}_per_season"] = per_season.get(f"{stat}_per_season", 0) + value
        
        # Calculate averages
        averages = {}
        season_count = len(seasons)
        
        if season_count > 0:
            for stat, total in per_season.items():
                averages[stat] = round(total / season_count, 1)
        
        # Per-game averages
        if total_games > 0:
            for stat, total_value in per_season.items():
                stat_name = stat.replace('_per_season', '')
                averages[f"{stat_name}_per_game"] = round(total_value / total_games, 1)
        
        return averages
    
    def _generate_basic_projections(self, averages: Dict, position: str) -> Dict:
        """Generate basic projections from historical averages"""
        projections = {}
        
        # Project for 16-17 game season
        games_projected = 16
        
        for stat, avg_value in averages.items():
            if '_per_game' in stat:
                base_stat = stat.replace('_per_game', '')
                projections[f"projected_{base_stat}"] = round(avg_value * games_projected, 1)
            elif '_per_season' in stat:
                base_stat = stat.replace('_per_season', '')
                projections[f"projected_{base_stat}"] = round(avg_value, 1)
        
        return projections
    
    def _load_cached_stats(self, cache_key: str) -> Optional[Dict]:
        """Load cached statistics if still valid"""
        cache_file = os.path.join(self.stats_cache_dir, f"{cache_key}.json")
        
        if not os.path.exists(cache_file):
            return None
        
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            cache_time = datetime.fromisoformat(cache_data['cached_at'])
            if datetime.now() - cache_time < self.cache_duration:
                return cache_data['data']
        
        except Exception as e:
            logger.debug(f"Error reading stats cache for {cache_key}: {e}")
        
        return None
    
    def _cache_stats(self, cache_key: str, data: Dict):
        """Cache statistics data"""
        cache_file = os.path.join(self.stats_cache_dir, f"{cache_key}.json")
        
        try:
            cache_data = {
                'data': data,
                'cached_at': datetime.now().isoformat()
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.debug(f"Cached stats for {cache_key}")
            
        except Exception as e:
            logger.warning(f"Error caching stats for {cache_key}: {e}")
    
    def get_position_rankings(self, position: str, stat: str = 'fantasy_points', year: Optional[int] = None) -> List[Dict]:
        """Get position rankings by specified stat"""
        if year is None:
            year = datetime.now().year - 1  # Previous year data
        
        # This would need to be implemented with actual stats data
        # For now, return empty list
        logger.info(f"Position rankings for {position} by {stat} not yet implemented")
        return []