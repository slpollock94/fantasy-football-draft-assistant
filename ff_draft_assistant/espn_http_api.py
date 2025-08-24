
from datetime import datetime
from typing import Dict, Any

import requests

class ESPNAPI:
    @staticmethod
    def _base_url(season: int) -> str:
        """Construct the base ESPN API URL for a given season."""
        return (
            f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/segments/0/leagues"
        )

    @staticmethod
    def get_league(league_id: str, season: int | None = None) -> Dict[str, Any]:
        season = season or datetime.now().year
        url = f"{ESPNAPI._base_url(season)}/{league_id}"

        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_draft(league_id: str, season: int | None = None) -> Dict[str, Any]:
        season = season or datetime.now().year
        url = f"{ESPNAPI._base_url(season)}/{league_id}?view=mDraftDetail"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

# Example usage:
# league = ESPNAPI.get_league('your_league_id')
# draft = ESPNAPI.get_draft('your_league_id')
