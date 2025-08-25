#!/usr/bin/env python3
"""
Final cleanup script to ensure database quality
"""

import logging
from typing import List, Dict, Set
from mongo_utils import get_all_players, insert_players
from local_store import LocalDataStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def final_cleanup():
    """Final cleanup of database"""
    logger.info("Starting final database cleanup...")
    
    # Get all players
    players = get_all_players()
    logger.info(f"Current database size: {len(players)} players")
    
    # Step 1: Remove exact duplicates
    unique_players = []
    seen_players = set()
    
    for player in players:
        # Create unique key
        key = f"{player.get('name', '').lower().strip()}_{player.get('position', '')}_{player.get('team', '')}"
        
        if key not in seen_players:
            seen_players.add(key)
            unique_players.append(player)
        else:
            logger.debug(f"Removing duplicate: {player.get('name')} ({player.get('position')} - {player.get('team')})")
    
    logger.info(f"After duplicate removal: {len(unique_players)} players")
    
    # Step 2: Apply strict quality filters
    quality_players = []
    
    nfl_teams = {
        'ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE',
        'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC',
        'LV', 'LAC', 'LAR', 'MIA', 'MIN', 'NE', 'NO', 'NYG',
        'NYJ', 'PHI', 'PIT', 'SF', 'SEA', 'TB', 'TEN', 'WAS'
    }
    
    valid_positions = {'QB', 'RB', 'WR', 'TE', 'K', 'DEF'}
    
    for player in unique_players:
        # Must have valid basics
        name = (player.get('name') or '').strip()
        position = (player.get('position') or '').upper()
        team = (player.get('team') or '').upper()
        
        if not name or len(name) < 2:
            continue
            
        if position not in valid_positions:
            continue
            
        if team not in nfl_teams:
            continue
        
        # Quality indicators
        has_adp = player.get('adp') is not None
        has_sleeper_id = player.get('sleeper_id') is not None
        has_recent_source = player.get('source') in ['sleeper_api', 'adp_integration']
        
        # Include if has quality indicators
        if has_adp or has_sleeper_id or has_recent_source:
            quality_players.append(player)
    
    logger.info(f"After quality filtering: {len(quality_players)} players")
    
    # Step 3: Sort and rank
    def sort_key(player):
        pos_priority = {'QB': 1, 'RB': 2, 'WR': 3, 'TE': 4, 'K': 5, 'DEF': 6}
        pos_score = pos_priority.get(player.get('position', 'DEF'), 6)
        adp_score = player.get('adp', 999)
        return (pos_score, adp_score)
    
    quality_players.sort(key=sort_key)
    
    # Add overall rankings
    for i, player in enumerate(quality_players, 1):
        player['overall_rank'] = i
    
    # Add position rankings
    position_counters = {}
    for player in quality_players:
        position = player.get('position', 'DEF')
        position_counters[position] = position_counters.get(position, 0) + 1
        player['position_rank'] = position_counters[position]
    
    # Step 4: Clear and reload database
    logger.info("Clearing and reloading database with clean data...")
    local_store = LocalDataStore()
    local_store.clear_all_data()
    
    insert_players(quality_players)
    
    # Step 5: Generate final report
    print_final_report(quality_players)
    
    logger.info("Final cleanup completed successfully!")

def print_final_report(players: List[Dict]):
    """Print final database report"""
    print("\n" + "="*60)
    print("FINAL CLEAN DATABASE REPORT")
    print("="*60)
    
    print(f"Total clean players: {len(players)}")
    
    # Position breakdown
    positions = {}
    adp_count = 0
    teams = set()
    
    for player in players:
        pos = player.get('position', 'Unknown')
        positions[pos] = positions.get(pos, 0) + 1
        
        if player.get('adp'):
            adp_count += 1
        
        team = player.get('team')
        if team:
            teams.add(team)
    
    print(f"\nPosition breakdown:")
    for pos, count in sorted(positions.items()):
        print(f"  {pos}: {count}")
    
    print(f"\nData quality:")
    print(f"  Players with ADP: {adp_count}/{len(players)} ({adp_count/len(players)*100:.1f}%)")
    print(f"  NFL teams represented: {len(teams)}/32")
    
    print(f"\nTop 15 players (by ADP):")
    players_with_adp = [p for p in players if p.get('adp')]
    players_with_adp.sort(key=lambda x: x.get('adp', 999))
    
    for i, player in enumerate(players_with_adp[:15], 1):
        name = player.get('name')
        pos = player.get('position')
        team = player.get('team')
        adp = player.get('adp')
        print(f"  {i:2}. {name} ({pos} - {team}) ADP: {adp}")
    
    print(f"\nPosition leaders:")
    position_leaders = {}
    for player in players:
        pos = player.get('position')
        if pos not in position_leaders or (player.get('adp', 999) < position_leaders[pos].get('adp', 999)):
            position_leaders[pos] = player
    
    for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']:
        if pos in position_leaders:
            player = position_leaders[pos]
            print(f"  {pos}: {player.get('name')} ({player.get('team')}) ADP: {player.get('adp', 'N/A')}")
    
    print("="*60)

if __name__ == "__main__":
    final_cleanup()