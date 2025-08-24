import logging
from datetime import datetime
from typing import List, Dict, Any

import requests

class SleeperAPI:
    BASE_URL = "https://api.sleeper.app/v1"

    @staticmethod
    def get_players() -> List[Dict[str, Any]]:
        url = f"{SleeperAPI.BASE_URL}/players/nfl"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_drafts_by_user(username: str, season: int | None = None) -> List[Dict[str, Any]]:
        """Retrieve drafts for a user for a given season.

        Args:
            username: Sleeper username.
            season: Four-digit year of the season. Defaults to the current year.

        Returns:
            A list of draft dictionaries. Returns an empty list if the response is invalid
            or the request fails.
        """

        season = season or datetime.now().year
        url = f"{SleeperAPI.BASE_URL}/user/{username}/drafts/nfl/{season}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, list):
                raise ValueError("Invalid response format: expected a list of drafts")
            return data
        except (requests.RequestException, ValueError) as exc:
            logging.error("Failed to fetch drafts for user %s: %s", username, exc)
            return []

    @staticmethod
    def get_draft_picks(draft_id: str) -> List[Dict[str, Any]]:
        url = f"{SleeperAPI.BASE_URL}/draft/{draft_id}/picks"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

# Example usage:
# players = SleeperAPI.get_players()
# drafts = SleeperAPI.get_drafts_by_user('your_username')  # defaults to current season
# drafts_2023 = SleeperAPI.get_drafts_by_user('your_username', season=2023)
# picks = SleeperAPI.get_draft_picks('draft_id')
