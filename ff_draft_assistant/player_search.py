#!/usr/bin/env python3
"""
Enhanced Player Search Module

Provides advanced search, filtering, and ranking capabilities for the 
fantasy football draft assistant player database.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from mongo_utils import get_all_players

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlayerSearchEngine:
    """Advanced player search and filtering engine"""
    
    def __init__(self):
        self.players_cache = []
        self.last_update = None
        
    def refresh_cache(self) -> bool:
        """Refresh the players cache from database"""
        try:
            self.players_cache = get_all_players()
            logger.info(f"Refreshed cache with {len(self.players_cache)} players")
            return True
        except Exception as e:
            logger.error(f"Failed to refresh player cache: {e}")
            return False
    
    def search_players(self, 
                      query: str = "", 
                      position: str = "", 
                      team: str = "", 
                      max_results: int = 50,
                      sort_by: str = "projected_points",
                      sort_desc: bool = True,
                      available_only: bool = True) -> List[Dict[str, Any]]:
        """
        Advanced player search with multiple filters
        
        Args:
            query: Name search query (partial matches supported)
            position: Filter by position (QB, RB, WR, TE, K, DEF)
            team: Filter by team abbreviation
            max_results: Maximum number of results to return
            sort_by: Field to sort by (projected_points, avg_points, rank, name, age)
            sort_desc: Sort in descending order
            available_only: Only return undrafted players
            
        Returns:
            List of matching players
        """
        if not self.players_cache:
            self.refresh_cache()
        
        results = self.players_cache.copy()
        
        # Filter by availability
        if available_only:
            results = [p for p in results if not p.get('drafted', False)]
        
        # Filter by position
        if position:
            position = position.upper()
            results = [p for p in results if p.get('position', '').upper() == position]
        
        # Filter by team
        if team:
            team = team.upper()
            results = [p for p in results if (p.get('team') or '').upper() == team]
        
        # Filter by name query
        if query:
            query = query.lower().strip()
            filtered_results = []
            
            for player in results:
                name = player.get('name', '').lower()
                
                # Exact match gets highest priority
                if query == name:
                    player['search_score'] = 100
                    filtered_results.append(player)
                # Starts with query gets high priority
                elif name.startswith(query):
                    player['search_score'] = 90
                    filtered_results.append(player)
                # Contains query gets medium priority
                elif query in name:
                    player['search_score'] = 70
                    filtered_results.append(player)
                # Fuzzy match for typos
                elif self._fuzzy_match(query, name):
                    player['search_score'] = 50
                    filtered_results.append(player)
            
            results = filtered_results
            
            # If we have search scores, sort by them first
            if results and 'search_score' in results[0]:
                results.sort(key=lambda x: (x['search_score'], x.get(sort_by, 0)), 
                           reverse=True)
        
        # Sort by specified field if no search query
        if not query and sort_by:
            reverse_sort = sort_desc
            try:
                if sort_by in ['projected_points', 'avg_points', 'age', 'years_exp', 'weight']:
                    # Numeric sorting
                    results.sort(key=lambda x: float(x.get(sort_by, 0) or 0), reverse=reverse_sort)
                elif sort_by == 'rank':
                    # Rank sorting (lower rank number is better)
                    results.sort(key=lambda x: int(x.get(sort_by, 999) or 999), reverse=False)
                else:
                    # String sorting
                    results.sort(key=lambda x: str(x.get(sort_by, '')), reverse=reverse_sort)
            except (ValueError, TypeError) as e:
                logger.warning(f"Sort error for field {sort_by}: {e}")
                # Fallback to projected_points
                results.sort(key=lambda x: float(x.get('projected_points', 0) or 0), reverse=True)
        
        # Limit results
        return results[:max_results]
    
    def _fuzzy_match(self, query: str, name: str, threshold: float = 0.7) -> bool:
        """Simple fuzzy matching for typos"""
        # Remove spaces and convert to lowercase
        query = re.sub(r'\s+', '', query.lower())
        name = re.sub(r'\s+', '', name.lower())
        
        # Calculate similarity using a simple ratio
        if len(query) == 0 or len(name) == 0:
            return False
        
        # Check if query is substantially contained in name
        matches = 0
        for char in query:
            if char in name:
                matches += 1
        
        similarity = matches / len(query)
        return similarity >= threshold
    
    def get_top_players_by_position(self, position: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get top available players for a specific position"""
        return self.search_players(
            position=position,
            max_results=limit,
            sort_by="projected_points",
            available_only=True
        )
    
    def get_sleeper_picks(self, round_num: int = 1) -> List[Dict[str, Any]]:
        """Get potential sleeper picks (high upside, lower projected points)"""
        if not self.players_cache:
            self.refresh_cache()
        
        # Look for players with decent projections but lower ranks
        sleepers = []
        for player in self.players_cache:
            if player.get('drafted', False):
                continue
                
            proj_points = float(player.get('projected_points', 0) or 0)
            rank = int(player.get('rank', 999) or 999)
            age = int(player.get('age', 30) or 30)
            
            # Sleeper criteria: decent points, lower rank, younger age
            if proj_points > 100 and rank > 50 and age < 28:
                sleeper_score = proj_points + (30 - age) * 5 - rank * 0.5
                player['sleeper_score'] = round(sleeper_score, 1)
                sleepers.append(player)
        
        # Sort by sleeper score
        sleepers.sort(key=lambda x: x.get('sleeper_score', 0), reverse=True)
        return sleepers[:20]
    
    def get_handcuff_suggestions(self, player_name: str) -> List[Dict[str, Any]]:
        """Get handcuff suggestions for a drafted player"""
        if not self.players_cache:
            self.refresh_cache()
        
        # Find the player
        target_player = None
        for player in self.players_cache:
            if player.get('name', '').lower() == player_name.lower():
                target_player = player
                break
        
        if not target_player:
            return []
        
        # Only RBs typically have meaningful handcuffs
        if target_player.get('position') != 'RB':
            return []
        
        team = target_player.get('team', '')
        if not team:
            return []
        
        # Find other RBs on the same team
        handcuffs = []
        for player in self.players_cache:
            if (player.get('position') == 'RB' and 
                player.get('team') == team and 
                player.get('name') != target_player.get('name') and
                not player.get('drafted', False)):
                handcuffs.append(player)
        
        # Sort by projected points
        handcuffs.sort(key=lambda x: float(x.get('projected_points', 0) or 0), reverse=True)
        return handcuffs[:5]
    
    def analyze_team_needs(self, drafted_players: List[str]) -> Dict[str, Any]:
        """Analyze team composition and suggest position priorities"""
        position_counts = {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'K': 0, 'DEF': 0}
        
        # Count drafted players by position
        for player_name in drafted_players:
            for player in self.players_cache:
                if player.get('name', '').lower() == player_name.lower():
                    pos = player.get('position', '')
                    if pos in position_counts:
                        position_counts[pos] += 1
                    break
        
        # Standard roster construction recommendations
        position_targets = {'QB': 2, 'RB': 6, 'WR': 6, 'TE': 2, 'K': 1, 'DEF': 2}
        
        needs = {}
        priorities = []
        
        for pos, target in position_targets.items():
            current = position_counts[pos]
            need = max(0, target - current)
            needs[pos] = {
                'current': current,
                'target': target,
                'need': need,
                'priority': 'high' if need >= 2 else 'medium' if need == 1 else 'low'
            }
            
            if need > 0:
                priorities.append((pos, need, 'high' if need >= 2 else 'medium'))
        
        # Sort priorities by need
        priorities.sort(key=lambda x: x[1], reverse=True)
        
        return {
            'position_counts': position_counts,
            'needs': needs,
            'priorities': [{'position': p[0], 'need': p[1], 'priority': p[2]} for p in priorities]
        }
    
    def get_value_picks(self, round_num: int = 5) -> List[Dict[str, Any]]:
        """Get value picks based on ADP vs projected points"""
        if not self.players_cache:
            self.refresh_cache()
        
        value_picks = []
        for player in self.players_cache:
            if player.get('drafted', False):
                continue
            
            proj_points = float(player.get('projected_points', 0) or 0)
            rank = int(player.get('rank', 999) or 999)
            
            # Value = projection is higher than rank suggests
            if proj_points > 0 and rank > 0:
                expected_points_by_rank = max(50, 300 - rank * 2)  # Simple model
                value_score = proj_points - expected_points_by_rank
                
                if value_score > 20:  # Significant positive value
                    player['value_score'] = round(value_score, 1)
                    value_picks.append(player)
        
        # Sort by value score
        value_picks.sort(key=lambda x: x.get('value_score', 0), reverse=True)
        return value_picks[:15]
    
    def search_summary(self) -> Dict[str, Any]:
        """Get summary statistics of the player database"""
        if not self.players_cache:
            self.refresh_cache()
        
        total_players = len(self.players_cache)
        available_players = len([p for p in self.players_cache if not p.get('drafted', False)])
        
        position_counts = {}
        available_by_position = {}
        
        for player in self.players_cache:
            pos = player.get('position', 'Unknown')
            position_counts[pos] = position_counts.get(pos, 0) + 1
            
            if not player.get('drafted', False):
                available_by_position[pos] = available_by_position.get(pos, 0) + 1
        
        return {
            'total_players': total_players,
            'available_players': available_players,
            'drafted_players': total_players - available_players,
            'position_counts': position_counts,
            'available_by_position': available_by_position
        }

# Utility functions for the web interface
def format_player_display(player: Dict[str, Any]) -> Dict[str, Any]:
    """Format player data for web display"""
    return {
        'name': player.get('name', ''),
        'position': player.get('position', ''),
        'team': player.get('team', ''),
        'age': player.get('age', ''),
        'projected_points': player.get('projected_points', 0),
        'avg_points': player.get('avg_points', 0),
        'rank': player.get('rank', ''),
        'status': player.get('status', 'Active'),
        'injury_status': player.get('injury_status', ''),
        'drafted': player.get('drafted', False),
        'search_score': player.get('search_score'),
        'value_score': player.get('value_score'),
        'sleeper_score': player.get('sleeper_score')
    }

def quick_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Quick search function for API endpoints"""
    search_engine = PlayerSearchEngine()
    results = search_engine.search_players(query=query, max_results=limit)
    return [format_player_display(player) for player in results]

def position_search(position: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Position-specific search for API endpoints"""
    search_engine = PlayerSearchEngine()
    results = search_engine.get_top_players_by_position(position=position, limit=limit)
    return [format_player_display(player) for player in results]

def main():
    """Test the search functionality"""
    print("Player Search Engine Test")
    print("=" * 50)
    
    search_engine = PlayerSearchEngine()
    
    # Test basic search
    print("\n1. Testing name search for 'josh':")
    results = search_engine.search_players(query="josh", max_results=5)
    for player in results:
        print(f"  {player['name']} ({player['position']}, {player['team']}) - {player['projected_points']} pts")
    
    # Test position search
    print("\n2. Testing top 5 available QBs:")
    results = search_engine.get_top_players_by_position('QB', 5)
    for player in results:
        print(f"  {player['name']} ({player['team']}) - {player['projected_points']} pts")
    
    # Test summary
    print("\n3. Database summary:")
    summary = search_engine.search_summary()
    print(f"  Total players: {summary['total_players']}")
    print(f"  Available players: {summary['available_players']}")
    print("  By position:")
    for pos, count in summary['position_counts'].items():
        available = summary['available_by_position'].get(pos, 0)
        print(f"    {pos}: {available}/{count} available")

if __name__ == "__main__":
    main()
