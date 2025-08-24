import requests
from typing import List, Dict, Any

class SleeperAPI:
    BASE_URL = "https://api.sleeper.app/v1"

    @staticmethod
    def get_players() -> List[Dict[str, Any]]:
        url = f"{SleeperAPI.BASE_URL}/players/nfl"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_drafts_by_user(username: str) -> List[Dict[str, Any]]:
        url = f"{SleeperAPI.BASE_URL}/user/{username}/drafts/nfl/2025"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_draft_picks(draft_id: str) -> List[Dict[str, Any]]:
        url = f"{SleeperAPI.BASE_URL}/draft/{draft_id}/picks"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

# Example usage:
# players = SleeperAPI.get_players()
# drafts = SleeperAPI.get_drafts_by_user('your_username')
# picks = SleeperAPI.get_draft_picks('draft_id')
