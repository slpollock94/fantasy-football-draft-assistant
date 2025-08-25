#!/usr/bin/env python3
"""
Fresh database loader - Clear and reload with high-quality NFL player data
"""

import requests
import logging
from typing import List, Dict, Optional
from mongo_utils import insert_players, get_all_players
from adp_integration import ADPDataSource
from local_store import LocalDataStore
import json
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FreshDatabaseLoader:
    """Load fresh, high-quality NFL player data from multiple sources"""
    
    def __init__(self):
        self.sleeper_url = "https://api.sleeper.app/v1/players/nfl"
        self.adp_source = ADPDataSource()
        self.local_store = LocalDataStore()
        
        # NFL teams for validation
        self.nfl_teams = {
            'ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE',
            'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC',
            'LV', 'LAC', 'LAR', 'MIA', 'MIN', 'NE', 'NO', 'NYG',
            'NYJ', 'PHI', 'PIT', 'SF', 'SEA', 'TB', 'TEN', 'WAS'
        }
        
        # Fantasy relevant positions
        self.fantasy_positions = {'QB', 'RB', 'WR', 'TE', 'K', 'DEF'}
        
        # Minimum thresholds for player inclusion
        self.min_thresholds = {
            'QB': {'years_exp': 0, 'depth_chart_order': 4},  # Top 4 QBs per team
            'RB': {'years_exp': 0, 'depth_chart_order': 5},  # Top 5 RBs per team
            'WR': {'years_exp': 0, 'depth_chart_order': 6},  # Top 6 WRs per team
            'TE': {'years_exp': 0, 'depth_chart_order': 4},  # Top 4 TEs per team
            'K': {'years_exp': 0, 'depth_chart_order': 2},   # Top 2 Ks per team
            'DEF': {'years_exp': 0, 'depth_chart_order': 1}  # 1 DEF per team
        }
    
    def clear_database(self):
        """Clear existing database"""
        logger.info("Clearing existing database...")
        
        try:
            # Clear local store
            self.local_store.clear_all_data()
            logger.info("Database cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing database: {e}")
            raise
    
    def load_fresh_data(self) -> Dict:
        """Load fresh, high-quality player data"""
        logger.info("Loading fresh NFL player data from Sleeper API...")
        
        try:
            # Step 1: Fetch from Sleeper API
            response = requests.get(self.sleeper_url, timeout=30)
            response.raise_for_status()
            sleeper_data = response.json()
            
            logger.info(f"Retrieved {len(sleeper_data)} players from Sleeper API")
            
            # Step 2: Process and filter players
            processed_players = self._process_sleeper_data(sleeper_data)
            
            # Step 3: Add ADP data
            players_with_adp = self._add_adp_data(processed_players)
            
            # Step 4: Final quality check
            final_players = self._final_quality_check(players_with_adp)
            
            # Step 5: Save to database
            insert_players(final_players)
            
            logger.info(f"Successfully loaded {len(final_players)} high-quality players")
            
            # Generate summary report
            report = self._generate_load_report(sleeper_data, final_players)
            
            return report
            
        except Exception as e:
            logger.error(f"Error loading fresh data: {e}")
            raise
    
    def _process_sleeper_data(self, sleeper_data: Dict) -> List[Dict]:
        """Process raw Sleeper data into clean player records"""
        processed_players = []
        position_counts = {}
        
        for player_id, player_info in sleeper_data.items():
            if not isinstance(player_info, dict):
                continue
            
            # Extract basic info
            player = self._extract_player_info(player_id, player_info)
            
            if not player:
                continue
            
            # Apply quality filters
            if not self._passes_quality_filters(player):
                continue
            
            # Track position counts for depth chart management
            pos = player['position']
            team = player['team']
            position_key = f"{team}_{pos}"
            position_counts[position_key] = position_counts.get(position_key, 0) + 1
            
            # Apply depth chart limits
            max_depth = self.min_thresholds.get(pos, {}).get('depth_chart_order', 10)
            if position_counts[position_key] <= max_depth:
                processed_players.append(player)
            else:
                logger.debug(f"Skipping {player['name']} - depth chart limit reached for {pos} on {team}")
        
        logger.info(f"Processed {len(processed_players)} players from Sleeper data")
        return processed_players
    
    def _extract_player_info(self, player_id: str, player_info: Dict) -> Optional[Dict]:
        """Extract and clean player information"""
        try:
            # Basic required fields
            position = player_info.get('position')
            team = player_info.get('team')
            
            # Must have valid position and team
            if not position or not team or position not in self.fantasy_positions:
                return None
            
            if team not in self.nfl_teams:
                return None
            
            # Player name
            full_name = player_info.get('full_name')
            if not full_name:
                first = player_info.get('first_name', '')
                last = player_info.get('last_name', '')
                full_name = f"{first} {last}".strip()
            
            if not full_name or len(full_name) < 2:
                return None
            
            # Status check - must be active
            status = player_info.get('status', '').upper()
            if status in ['RETIRED', 'SUSPENDED', 'INACTIVE']:
                return None
            
            # Build player record
            player = {
                'sleeper_id': player_id,
                'name': full_name.strip(),
                'position': position,
                'team': team,
                'status': status or 'Active',
                'years_exp': player_info.get('years_exp', 0),
                'age': player_info.get('age'),
                'height': player_info.get('height'),
                'weight': player_info.get('weight'),
                'college': player_info.get('college'),
                'jersey_number': player_info.get('number'),
                'drafted': False,  # Default to not drafted
                'source': 'sleeper_api',
                'last_updated': datetime.now().isoformat()
            }
            
            # Add position-specific stats if available
            self._add_position_stats(player, player_info)
            
            return player
            
        except Exception as e:
            logger.debug(f"Error processing player {player_id}: {e}")
            return None
    
    def _add_position_stats(self, player: Dict, player_info: Dict):
        """Add position-specific statistics"""
        position = player['position']
        
        # Common stats
        stats_mapping = {
            'gp': 'games_played',
            'pts_ppr': 'fantasy_points_ppr',
            'pts_std': 'fantasy_points_std',
            'pts_half_ppr': 'fantasy_points_half_ppr'
        }
        
        for sleeper_key, player_key in stats_mapping.items():
            value = player_info.get(sleeper_key)
            if value is not None and value > 0:
                player[player_key] = value
        
        # Position specific stats
        if position == 'QB':
            qb_stats = {
                'pass_yd': 'passing_yards',
                'pass_td': 'passing_touchdowns',
                'pass_int': 'interceptions',
                'rush_yd': 'rushing_yards',
                'rush_td': 'rushing_touchdowns'
            }
            for sleeper_key, player_key in qb_stats.items():
                value = player_info.get(sleeper_key)
                if value is not None and value > 0:
                    player[player_key] = value
                    
        elif position == 'RB':
            rb_stats = {
                'rush_yd': 'rushing_yards',
                'rush_td': 'rushing_touchdowns', 
                'rec': 'receptions',
                'rec_yd': 'receiving_yards',
                'rec_td': 'receiving_touchdowns'
            }
            for sleeper_key, player_key in rb_stats.items():
                value = player_info.get(sleeper_key)
                if value is not None and value > 0:
                    player[player_key] = value
                    
        elif position in ['WR', 'TE']:
            rec_stats = {
                'rec': 'receptions',
                'rec_yd': 'receiving_yards',
                'rec_td': 'receiving_touchdowns',
                'rush_yd': 'rushing_yards',
                'rush_td': 'rushing_touchdowns'
            }
            for sleeper_key, player_key in rec_stats.items():
                value = player_info.get(sleeper_key)
                if value is not None and value > 0:
                    player[player_key] = value
                    
        elif position == 'K':
            k_stats = {
                'fgm': 'field_goals_made',
                'fga': 'field_goals_attempted',
                'xpm': 'extra_points_made',
                'xpa': 'extra_points_attempted'
            }
            for sleeper_key, player_key in k_stats.items():
                value = player_info.get(sleeper_key)
                if value is not None and value > 0:
                    player[player_key] = value
    
    def _passes_quality_filters(self, player: Dict) -> bool:
        """Apply quality filters to determine if player should be included"""
        
        # Must have valid name, position, team
        if not all([player.get('name'), player.get('position'), player.get('team')]):
            return False
        
        # Age filter - reasonable NFL age range
        age = player.get('age')
        if age and (age < 20 or age > 40):
            logger.debug(f"Age filter: {player['name']} age {age}")
            return False
        
        # Experience filter - include rookies but be selective
        years_exp = player.get('years_exp', 0)
        
        # For rookies (0 years exp), require some stats or known college
        if years_exp == 0:
            has_stats = any(player.get(stat, 0) > 0 for stat in ['fantasy_points_ppr', 'games_played'])
            has_college = bool(player.get('college'))
            
            if not (has_stats or has_college):
                logger.debug(f"Rookie filter: {player['name']} - no stats or college info")
                return False
        
        # Very high experience might indicate old/inactive players
        if years_exp > 20:
            logger.debug(f"Experience filter: {player['name']} - {years_exp} years experience")
            return False
        
        return True
    
    def _add_adp_data(self, players: List[Dict]) -> List[Dict]:
        """Add ADP data to players"""
        logger.info("Adding ADP data...")
        
        try:
            # Get consensus ADP data
            multi_format_adp = self.adp_source.get_multi_format_adp()
            
            if multi_format_adp:
                consensus_adp = self.adp_source.calculate_consensus_adp(multi_format_adp)
                players_with_adp = self.adp_source.merge_adp_with_players(players, consensus_adp)
                logger.info(f"Successfully added ADP data")
                return players_with_adp
            else:
                logger.warning("Could not retrieve ADP data")
                return players
                
        except Exception as e:
            logger.warning(f"Error adding ADP data: {e}")
            return players
    
    def _final_quality_check(self, players: List[Dict]) -> List[Dict]:
        """Final quality check and ranking"""
        logger.info("Performing final quality check...")
        
        valid_players = []
        
        for player in players:
            # Final validation
            if self._is_high_quality_player(player):
                valid_players.append(player)
        
        # Sort players by fantasy relevance
        valid_players.sort(key=self._fantasy_sort_key)
        
        # Add rankings
        for i, player in enumerate(valid_players, 1):
            player['overall_rank'] = i
        
        # Add position rankings
        self._add_position_rankings(valid_players)
        
        logger.info(f"Final quality check complete: {len(valid_players)} players")
        return valid_players
    
    def _is_high_quality_player(self, player: Dict) -> bool:
        """Determine if player meets high quality standards"""
        
        # Must have core info
        if not all([player.get('name'), player.get('position'), player.get('team')]):
            return False
        
        # Team must be valid
        if player.get('team') not in self.nfl_teams:
            return False
        
        # Position must be fantasy relevant
        if player.get('position') not in self.fantasy_positions:
            return False
        
        # Prefer players with some statistical data or ADP
        has_fantasy_relevance = any([
            player.get('fantasy_points_ppr', 0) > 0,
            player.get('games_played', 0) > 0,
            player.get('adp'),
            player.get('years_exp', 0) >= 1
        ])
        
        return has_fantasy_relevance
    
    def _fantasy_sort_key(self, player: Dict):
        """Sort key for fantasy relevance"""
        # Position priority
        position_priority = {'QB': 1, 'RB': 2, 'WR': 3, 'TE': 4, 'K': 5, 'DEF': 6}
        pos_score = position_priority.get(player.get('position', 'DEF'), 6)
        
        # ADP score (lower ADP = higher priority)
        adp_score = player.get('adp', 999)
        
        # Fantasy points score
        fantasy_score = -(player.get('fantasy_points_ppr', 0))  # Negative for desc order
        
        return (pos_score, adp_score, fantasy_score)
    
    def _add_position_rankings(self, players: List[Dict]):
        """Add position-specific rankings"""
        position_counters = {}
        
        for player in players:
            position = player.get('position', 'DEF')
            position_counters[position] = position_counters.get(position, 0) + 1
            player['position_rank'] = position_counters[position]
    
    def _generate_load_report(self, raw_data: Dict, final_players: List[Dict]) -> Dict:
        """Generate comprehensive load report"""
        
        # Position breakdown
        position_counts = {}
        adp_count = 0
        stats_count = 0
        
        for player in final_players:
            pos = player.get('position', 'Unknown')
            position_counts[pos] = position_counts.get(pos, 0) + 1
            
            if player.get('adp'):
                adp_count += 1
            
            if player.get('fantasy_points_ppr', 0) > 0:
                stats_count += 1
        
        # Team breakdown
        team_counts = {}
        for player in final_players:
            team = player.get('team', 'Unknown')
            team_counts[team] = team_counts.get(team, 0) + 1
        
        return {
            'load_summary': {
                'raw_sleeper_players': len(raw_data),
                'final_loaded_players': len(final_players),
                'data_quality_rate': f"{len(final_players) / len(raw_data) * 100:.1f}%",
                'players_with_adp': adp_count,
                'players_with_stats': stats_count
            },
            'position_breakdown': position_counts,
            'team_breakdown': dict(sorted(team_counts.items())),
            'load_timestamp': datetime.now().isoformat()
        }
    
    def print_report(self, report: Dict):
        """Print load report"""
        print("\n" + "="*60)
        print("FRESH DATABASE LOAD REPORT")
        print("="*60)
        
        summary = report['load_summary']
        print(f"Raw Sleeper players: {summary['raw_sleeper_players']:,}")
        print(f"Final loaded players: {summary['final_loaded_players']:,}")
        print(f"Data quality rate: {summary['data_quality_rate']}")
        print(f"Players with ADP: {summary['players_with_adp']}")
        print(f"Players with stats: {summary['players_with_stats']}")
        
        print(f"\nPosition breakdown:")
        for pos, count in summary.get('position_breakdown', {}).items():
            print(f"  {pos}: {count}")
        
        print(f"\nTop 10 teams by player count:")
        team_breakdown = report.get('team_breakdown', {})
        sorted_teams = sorted(team_breakdown.items(), key=lambda x: x[1], reverse=True)
        for team, count in sorted_teams[:10]:
            print(f"  {team}: {count}")
        
        print(f"\nDatabase loaded at: {report.get('load_timestamp', 'Unknown')}")
        print("="*60)

def main():
    """Main execution"""
    loader = FreshDatabaseLoader()
    
    print("Starting fresh database load...")
    
    # Step 1: Clear existing database
    loader.clear_database()
    
    # Step 2: Load fresh data
    report = loader.load_fresh_data()
    
    # Step 3: Print report
    loader.print_report(report)
    
    print("\nFresh database load completed successfully!")

if __name__ == "__main__":
    main()