#!/usr/bin/env python3
"""
Test script for the enhanced fantasy football database features
"""

import logging
from adp_integration import ADPDataSource
from player_validator import PlayerDataValidator
from mongo_utils import get_all_players

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_adp_integration():
    """Test ADP data fetching and integration"""
    print("\n" + "="*50)
    print("TESTING ADP INTEGRATION")
    print("="*50)
    
    adp_source = ADPDataSource()
    
    # Test single format
    print("Testing PPR ADP data...")
    ppr_data = adp_source.get_adp_data('ppr', teams=12)
    
    if ppr_data:
        print(f"[OK] Retrieved {len(ppr_data)} PPR ADP entries")
        
        # Show top 10 players
        print("\nTop 10 PPR ADP players:")
        for i, player in enumerate(ppr_data[:10], 1):
            print(f"  {i:2}. {player['name']} ({player['position']} - {player['team']}) - ADP: {player.get('adp', 'N/A')}")
    else:
        print("[ERROR] Failed to retrieve PPR ADP data")
    
    # Test multi-format consensus
    print("\nTesting consensus ADP calculation...")
    multi_format = adp_source.get_multi_format_adp()
    
    if multi_format:
        consensus = adp_source.calculate_consensus_adp(multi_format)
        print(f"[OK] Generated consensus ADP for {len(consensus)} players")
        
        print("\nTop 10 Consensus ADP players:")
        for i, player in enumerate(consensus[:10], 1):
            adp_data_str = ', '.join([f"{fmt}: {adp:.1f}" for fmt, adp in player['adp_data'].items()])
            print(f"  {i:2}. {player['name']} ({player['position']}) - Consensus: {player['consensus_adp']:.1f}")
            print(f"      Formats: {adp_data_str}")
    else:
        print("[ERROR] Failed to generate consensus ADP")

def test_player_validation():
    """Test player data validation"""
    print("\n" + "="*50)
    print("TESTING PLAYER VALIDATION")
    print("="*50)
    
    validator = PlayerDataValidator()
    
    # Test with sample data
    test_players = [
        {'name': 'Christian McCaffrey', 'position': 'RB', 'team': 'SF'},
        {'name': 'josh allen', 'position': 'qb', 'team': 'buf'},  # Test normalization
        {'name': 'Cooper Kupp', 'position': 'WR', 'team': 'LAR'},
        {'name': 'Invalid Player', 'position': 'XYZ', 'team': 'ABC'},  # Should be filtered
        {'name': 'Duplicate Player', 'position': 'WR', 'team': 'DAL'},
        {'name': 'Duplicate Player', 'position': 'WR', 'team': 'DAL'},  # Duplicate
    ]
    
    print(f"Testing with {len(test_players)} sample players")
    
    # Test individual validation
    valid_count = 0
    for player in test_players:
        if validator.validate_player_data(player.copy()):
            valid_count += 1
    
    print(f"[OK] {valid_count}/{len(test_players)} players passed individual validation")
    
    # Test duplicate detection
    cleaned_players = validator.detect_duplicates(test_players)
    print(f"[OK] Duplicate detection: {len(test_players)} -> {len(cleaned_players)} players")
    
    for player in cleaned_players:
        print(f"  - {player['name']} ({player['position']} - {player['team']})")

def test_current_database():
    """Test current database state"""
    print("\n" + "="*50)
    print("TESTING CURRENT DATABASE")
    print("="*50)
    
    players = get_all_players()
    print(f"Total players in database: {len(players)}")
    
    if not players:
        print("No players found in database")
        return
    
    # Analyze data quality
    validator = PlayerDataValidator()
    position_counts = {}
    team_counts = {}
    adp_count = 0
    valid_count = 0
    
    for player in players:
        # Count by position
        pos = player.get('position', 'UNKNOWN')
        position_counts[pos] = position_counts.get(pos, 0) + 1
        
        # Count by team
        team = player.get('team', 'UNKNOWN')
        team_counts[team] = team_counts.get(team, 0) + 1
        
        # Count ADP data
        if player.get('adp'):
            adp_count += 1
        
        # Validate player
        if validator.validate_player_data(player.copy()):
            valid_count += 1
    
    print(f"Players with ADP data: {adp_count}")
    print(f"Valid players: {valid_count}/{len(players)} ({valid_count/len(players)*100:.1f}%)")
    
    print("\nTop positions:")
    for pos, count in sorted(position_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {pos}: {count}")
    
    print("\nTop teams:")
    for team, count in sorted(team_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {team}: {count}")
    
    # Show sample of players with ADP
    players_with_adp = [p for p in players if p.get('adp')]
    if players_with_adp:
        print(f"\nSample players with ADP data:")
        for player in players_with_adp[:5]:
            print(f"  - {player['name']} ({player['position']} - {player['team']}) - ADP: {player['adp']}")

def main():
    """Run all tests"""
    print("FANTASY FOOTBALL DATABASE ENHANCEMENT TESTING")
    print("=" * 60)
    
    try:
        test_adp_integration()
        test_player_validation()
        test_current_database()
        
        print("\n" + "="*60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*60)
        
    except Exception as e:
        print(f"\n[ERROR] Test failed with error: {e}")
        logger.exception("Test failure")

if __name__ == "__main__":
    main()