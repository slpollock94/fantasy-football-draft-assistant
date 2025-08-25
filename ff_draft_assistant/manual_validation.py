#!/usr/bin/env python3
"""
Manual validation script to identify and remove non-NFL players
"""

import logging
from typing import List, Dict, Set
from mongo_utils import get_all_players, insert_players

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ManualNFLValidator:
    """Manual validation for NFL players using known criteria"""
    
    def __init__(self):
        # Known NFL teams
        self.nfl_teams = {
            'ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE',
            'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC',
            'LV', 'LAC', 'LAR', 'MIA', 'MIN', 'NE', 'NO', 'NYG',
            'NYJ', 'PHI', 'PIT', 'SF', 'SEA', 'TB', 'TEN', 'WAS'
        }
        
        # Known non-NFL players to remove (manually identified)
        self.known_invalid_players = {
            'riley neal',  # Not active NFL player
            'deon jackson',  # Practice squad/inactive
            'malik willis',  # Check if still active
            # Add more as identified
        }
        
        # Valid fantasy positions
        self.valid_positions = {'QB', 'RB', 'WR', 'TE', 'K', 'DEF'}
    
    def validate_player(self, player: Dict) -> bool:
        """Validate if player should be kept"""
        name = (player.get('name') or '').lower().strip()
        position = (player.get('position') or '').upper()
        team = (player.get('team') or '').upper()
        
        # Remove known invalid players
        if name in self.known_invalid_players:
            logger.debug(f"Removing known invalid player: {name}")
            return False
        
        # Must have valid position
        if position not in self.valid_positions:
            logger.debug(f"Invalid position {position} for {name}")
            return False
        
        # Must have valid NFL team (no None, FA, or empty teams)
        if team not in self.nfl_teams:
            logger.debug(f"Invalid team {team} for {name}")
            return False
        
        # Additional checks for suspicious players
        if self._is_suspicious_player(player):
            return False
        
        return True
    
    def _is_suspicious_player(self, player: Dict) -> bool:
        """Check for suspicious player indicators"""
        name = player.get('name', '').lower()
        
        # Check for common practice squad indicators
        suspicious_indicators = [
            'practice squad',
            'futures contract',
            'undrafted',
            'waiver',
        ]
        
        # If player has very low or no stats and no ADP, might be practice squad
        has_stats = any(player.get(stat, 0) > 0 for stat in ['projected_points', 'fantasy_points', 'adp'])
        
        if not has_stats and any(indicator in name for indicator in suspicious_indicators):
            logger.debug(f"Suspicious player detected: {name}")
            return True
        
        return False
    
    def clean_database(self) -> Dict:
        """Clean the database and return report"""
        logger.info("Starting manual NFL player validation...")
        
        # Get all players
        all_players = get_all_players()
        logger.info(f"Total players in database: {len(all_players)}")
        
        # Validate each player
        valid_players = []
        removed_players = []
        
        for player in all_players:
            if self.validate_player(player):
                valid_players.append(player)
            else:
                removed_players.append({
                    'name': player.get('name', 'Unknown'),
                    'position': player.get('position', 'Unknown'),
                    'team': player.get('team', 'Unknown'),
                    'reason': 'Manual validation failed'
                })
        
        logger.info(f"Validation complete: {len(valid_players)} valid, {len(removed_players)} removed")
        
        # Update database with clean players
        if valid_players:
            insert_players(valid_players)
            logger.info("Database updated with validated players")
        
        # Generate report
        report = {
            'original_count': len(all_players),
            'valid_count': len(valid_players),
            'removed_count': len(removed_players),
            'removal_rate': len(removed_players) / len(all_players) * 100 if all_players else 0,
            'removed_players_sample': removed_players[:20],  # Show first 20 removed
            'position_summary': self._generate_position_summary(valid_players)
        }
        
        return report
    
    def _generate_position_summary(self, players: List[Dict]) -> Dict:
        """Generate position breakdown"""
        position_counts = {}
        for player in players:
            pos = player.get('position', 'Unknown')
            position_counts[pos] = position_counts.get(pos, 0) + 1
        
        return position_counts
    
    def print_report(self, report: Dict):
        """Print cleaning report"""
        print("\n" + "="*60)
        print("MANUAL NFL VALIDATION REPORT")
        print("="*60)
        
        print(f"Original players: {report['original_count']}")
        print(f"Valid players: {report['valid_count']}")
        print(f"Removed players: {report['removed_count']}")
        print(f"Removal rate: {report['removal_rate']:.1f}%")
        
        print(f"\nPosition breakdown:")
        for pos, count in sorted(report['position_summary'].items()):
            print(f"  {pos}: {count}")
        
        print(f"\nSample of removed players:")
        for player in report['removed_players_sample']:
            print(f"  - {player['name']} ({player['position']} - {player['team']})")
        
        print("="*60)

def main():
    validator = ManualNFLValidator()
    report = validator.clean_database()
    validator.print_report(report)

if __name__ == "__main__":
    main()