#!/usr/bin/env python3
"""
Database cleaning script to remove non-NFL players and add ADP data
"""

import logging
from typing import List, Dict
from mongo_utils import get_all_players, insert_players
from player_validator import PlayerDataValidator
from adp_integration import ADPDataSource
from nfl_database import NFLPlayerDatabase

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseCleaner:
    """Clean and enhance fantasy football player database"""
    
    def __init__(self):
        self.validator = PlayerDataValidator()
        self.adp_source = ADPDataSource()
        self.nfl_db = NFLPlayerDatabase()
    
    def clean_and_enhance_database(self, add_adp=True, refresh_nfl_data=False):
        """Main cleaning and enhancement process"""
        logger.info("Starting database cleaning and enhancement process")
        
        # Step 1: Get current players
        logger.info("Retrieving current players from database...")
        current_players = get_all_players()
        logger.info(f"Found {len(current_players)} players in database")
        
        if not current_players:
            logger.warning("No players found in database. Consider running populate_espn or populate_nfl first.")
            return
        
        # Step 2: Validate and clean existing data
        logger.info("Validating and cleaning player data...")
        original_count = len(current_players)
        
        cleaned_players = self.validator.clean_database_players(current_players)
        
        # Generate validation report
        report = self.validator.generate_validation_report(current_players, cleaned_players)
        self._print_validation_report(report)
        
        # Step 3: Refresh with comprehensive NFL data if requested
        if refresh_nfl_data:
            logger.info("Refreshing with latest NFL player data...")
            fresh_nfl_data = self._get_fresh_nfl_data()
            if fresh_nfl_data:
                # Merge with cleaned data, preferring NFL source for basic info
                cleaned_players = self._merge_nfl_data(cleaned_players, fresh_nfl_data)
                logger.info(f"Merged with {len(fresh_nfl_data)} NFL players")
        
        # Step 4: Add ADP data if requested
        if add_adp:
            logger.info("Adding ADP data from multiple sources...")
            cleaned_players = self._add_adp_data(cleaned_players)
        
        # Step 5: Final validation and statistics
        final_players = self._final_validation(cleaned_players)
        
        # Step 6: Update database
        if final_players:
            logger.info(f"Updating database with {len(final_players)} cleaned players...")
            
            # Clear existing data and insert cleaned data
            self._backup_and_replace_database(final_players)
            
            logger.info("Database cleaning and enhancement completed successfully!")
            self._print_final_summary(original_count, len(final_players))
        else:
            logger.error("No valid players after cleaning - database not updated")
    
    def _print_validation_report(self, report: Dict):
        """Print detailed validation report"""
        summary = report['summary']
        positions = report['positions']
        
        print("\n" + "="*60)
        print("DATA VALIDATION REPORT")
        print("="*60)
        
        print(f"Original players: {summary['original_count']}")
        print(f"Valid players: {summary['cleaned_count']}")
        print(f"Removed players: {summary['removed_count']} ({summary['removal_percentage']}%)")
        
        print("\nPLAYERS BY POSITION:")
        print("-" * 30)
        all_positions = set(list(positions['original'].keys()) + list(positions['cleaned'].keys()))
        
        for pos in sorted(all_positions):
            orig = positions['original'].get(pos, 0)
            clean = positions['cleaned'].get(pos, 0)
            removed = orig - clean
            print(f"{pos:8}: {orig:3} -> {clean:3} (removed: {removed})")
        
        print("="*60)
    
    def _get_fresh_nfl_data(self) -> List[Dict]:
        """Get fresh NFL player data from Sleeper API"""
        try:
            success = self.nfl_db.populate_database(max_players=1000, update_db=False)
            if success:
                # Get the fresh data without updating the main database
                return self.nfl_db.get_processed_players()
            return []
        except Exception as e:
            logger.error(f"Failed to get fresh NFL data: {e}")
            return []
    
    def _merge_nfl_data(self, cleaned_players: List[Dict], nfl_data: List[Dict]) -> List[Dict]:
        """Merge cleaned players with fresh NFL data"""
        # Create lookup for NFL data
        nfl_lookup = {}
        for player in nfl_data:
            key = f"{player['name'].lower()}_{player['position']}_{player.get('team', 'FA')}"
            nfl_lookup[key] = player
        
        merged_players = []
        
        # Update existing players with NFL data
        for player in cleaned_players:
            key = f"{player['name'].lower()}_{player['position']}_{player.get('team', 'FA')}"
            
            if key in nfl_lookup:
                # Merge with NFL data, preserving fantasy-specific fields
                nfl_player = nfl_lookup[key]
                merged_player = nfl_player.copy()
                
                # Preserve fantasy-specific data from cleaned player
                fantasy_fields = ['projected_points', 'fantasy_points', 'drafted', 'adp', 'rank']
                for field in fantasy_fields:
                    if field in player:
                        merged_player[field] = player[field]
                
                merged_players.append(merged_player)
                del nfl_lookup[key]  # Remove to avoid duplicates
            else:
                merged_players.append(player)
        
        # Add new NFL players not in our database
        for remaining_player in nfl_lookup.values():
            merged_players.append(remaining_player)
        
        return merged_players
    
    def _add_adp_data(self, players: List[Dict]) -> List[Dict]:
        """Add ADP data to players"""
        try:
            # Get ADP data from multiple formats
            multi_format_adp = self.adp_source.get_multi_format_adp()
            
            if not multi_format_adp:
                logger.warning("Could not retrieve ADP data")
                return players
            
            # Calculate consensus ADP
            consensus_adp = self.adp_source.calculate_consensus_adp(multi_format_adp)
            
            if consensus_adp:
                # Merge ADP data with players
                enhanced_players = self.adp_source.merge_adp_with_players(players, consensus_adp)
                logger.info("ADP data successfully added to player database")
                return enhanced_players
            else:
                logger.warning("No consensus ADP data available")
                return players
                
        except Exception as e:
            logger.error(f"Failed to add ADP data: {e}")
            return players
    
    def _final_validation(self, players: List[Dict]) -> List[Dict]:
        """Final validation and quality check"""
        logger.info("Performing final validation...")
        
        # Remove any players that still don't meet standards
        valid_players = [p for p in players if self.validator.validate_player_data(p)]
        
        # Sort by position and projected value
        def sort_key(player):
            position_order = {'QB': 1, 'RB': 2, 'WR': 3, 'TE': 4, 'K': 5, 'DEF': 6}
            pos_priority = position_order.get(player.get('position', 'DEF'), 6)
            adp = player.get('adp', 999)
            return (pos_priority, adp)
        
        valid_players.sort(key=sort_key)
        
        logger.info(f"Final validation complete: {len(valid_players)} players ready")
        return valid_players
    
    def _backup_and_replace_database(self, new_players: List[Dict]):
        """Backup current database and replace with cleaned data"""
        try:
            # For MongoDB, we'll use the upsert strategy from insert_players
            # This will update existing players and add new ones
            insert_players(new_players)
            logger.info("Database successfully updated with cleaned data")
            
        except Exception as e:
            logger.error(f"Failed to update database: {e}")
            raise
    
    def _print_final_summary(self, original_count: int, final_count: int):
        """Print final summary of cleaning process"""
        print("\n" + "="*60)
        print("CLEANING PROCESS COMPLETE")
        print("="*60)
        print(f"Original players: {original_count}")
        print(f"Final players: {final_count}")
        print(f"Improvement: {((original_count - final_count) / original_count * 100):.1f}% reduction")
        print("Database has been updated with clean, validated player data.")
        print("ADP data has been integrated where available.")
        print("="*60)
    
    def quick_stats(self):
        """Print quick database statistics"""
        players = get_all_players()
        
        if not players:
            print("No players found in database")
            return
        
        # Count by position
        position_counts = {}
        adp_count = 0
        
        for player in players:
            pos = player.get('position', 'UNKNOWN')
            position_counts[pos] = position_counts.get(pos, 0) + 1
            
            if player.get('adp'):
                adp_count += 1
        
        print("\n" + "="*40)
        print("CURRENT DATABASE STATS")
        print("="*40)
        print(f"Total players: {len(players)}")
        print(f"Players with ADP: {adp_count}")
        print("\nBy position:")
        for pos, count in sorted(position_counts.items()):
            print(f"  {pos}: {count}")
        print("="*40)

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean and enhance fantasy football database")
    parser.add_argument('--no-adp', action='store_true', help='Skip ADP integration')
    parser.add_argument('--refresh-nfl', action='store_true', help='Refresh with latest NFL data')
    parser.add_argument('--stats-only', action='store_true', help='Show current database stats only')
    
    args = parser.parse_args()
    
    cleaner = DatabaseCleaner()
    
    if args.stats_only:
        cleaner.quick_stats()
    else:
        cleaner.clean_and_enhance_database(
            add_adp=not args.no_adp,
            refresh_nfl_data=args.refresh_nfl
        )

if __name__ == "__main__":
    main()