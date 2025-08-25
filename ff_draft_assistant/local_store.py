import json
import os
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class LocalDataStore:
    """Fallback local JSON data store when MongoDB is unavailable."""
    
    def __init__(self, file_path: str = "local_players.json"):
        self.file_path = file_path
        self.data = self._load_data()
    
    def _load_data(self) -> List[Dict]:
        """Load data from JSON file."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load local data: {e}")
                return []
        return []
    
    def _save_data(self):
        """Save data to JSON file."""
        try:
            with open(self.file_path, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save local data: {e}")
    
    def insert_players(self, players: List[Dict]):
        """Insert or update players in local store."""
        for new_player in players:
            # Find existing player by name and position
            existing_index = None
            for i, existing_player in enumerate(self.data):
                if (existing_player.get('name') == new_player.get('name') and 
                    existing_player.get('position') == new_player.get('position')):
                    existing_index = i
                    break
            
            if existing_index is not None:
                # Update existing player
                self.data[existing_index].update(new_player)
            else:
                # Add new player
                self.data.append(new_player)
        
        self._save_data()
        logger.info(f"Saved {len(players)} players to local store")
    
    def get_all_players(self) -> List[Dict]:
        """Get all players from local store."""
        return self.data.copy()
    
    def search_players(self, query: Dict) -> List[Dict]:
        """Search players in local store."""
        results = []
        for player in self.data:
            match = True
            for key, value in query.items():
                if player.get(key) != value:
                    match = False
                    break
            if match:
                results.append(player)
        return results
    
    def update_player_drafted_status(self, player_name: str, drafted: bool) -> bool:
        """Update a player's drafted status in local store."""
        for player in self.data:
            if player.get('name') == player_name:
                player['drafted'] = drafted
                self._save_data()
                logger.info(f"Updated {player_name} drafted status to {drafted}")
                return True
        logger.warning(f"Player {player_name} not found in local store")
        return False
    
    def clear_all_data(self):
        """Clear all data from local store."""
        self.data = []
        self._save_data()
        logger.info("Cleared all data from local store")

# Global fallback instance
local_store = LocalDataStore()
