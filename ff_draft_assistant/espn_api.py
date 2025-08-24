import requests
from typing import List, Dict, Any

class ESPNAPI:
    BASE_URL = "https://fantasy.espn.com/apis/v3/games/ffl/seasons/2025/segments/0/leagues"

    @staticmethod
    def get_league(league_id: str) -> Dict[str, Any]:
        url = f"{ESPNAPI.BASE_URL}/{league_id}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_draft(league_id: str) -> Dict[str, Any]:
        url = f"{ESPNAPI.BASE_URL}/{league_id}?view=mDraftDetail"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

# Example usage:
# league = ESPNAPI.get_league('your_league_id')
# draft = ESPNAPI.get_draft('your_league_id')
