import os
from typing import Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from espn_api.football import League
from mongo_utils import insert_players

load_dotenv()

def populate_from_espn(league_id: str, year: int = 2024, free_agent_limit: int = 50):
    """Populate MongoDB with players from an ESPN league.

    Parameters
    ----------
    league_id: str
        ESPN league identifier.
    year: int, optional
        League season year.
    free_agent_limit: int, optional
        Maximum number of free agents to fetch. Defaults to 50. Use ``None`` to
        fetch all available free agents.
    """

    # For private leagues, you may need ESPN cookies
    espn_s2 = os.getenv("ESPN_S2")
    swid = os.getenv("SWID")

    try:
        if espn_s2 and swid:
            league = League(
                league_id=league_id, year=season, espn_s2=espn_s2, swid=swid
            )
        else:
            league = League(league_id=league_id, year=year)

        players: Dict[Any, Dict[str, Any]] = {}

        def add_or_merge(player_obj, drafted: bool):
            key = (
                getattr(player_obj, "playerId", None)
                or getattr(player_obj, "id", None)
                or f"{player_obj.name}-{player_obj.position}"
            )

            player_data = {
                "rank": str(getattr(player_obj, "draft_pick", "")),
                "name": player_obj.name,
                "position": player_obj.position,
                "team": getattr(player_obj, "proTeam", ""),
                "projected_points": getattr(player_obj, "projected_total_points", 0),
                "avg_points": getattr(player_obj, "avg_points", 0),
                "drafted": drafted,
            }

            existing = players.get(key)
            if existing:
                existing["drafted"] = existing.get("drafted") or drafted
                if not existing.get("rank") and player_data["rank"]:
                    existing["rank"] = player_data["rank"]
                existing["projected_points"] = max(
                    existing.get("projected_points", 0), player_data["projected_points"]
                )
                existing["avg_points"] = max(
                    existing.get("avg_points", 0), player_data["avg_points"]
                )
            else:
                players[key] = player_data
        # Get all teams and their rosters
        for team in league.teams:
            for player in team.roster:
                add_or_merge(player, drafted=True)

        # Also get free agents if available
        try:
            free_agents = league.free_agents()
            if free_agent_limit is not None:
                free_agents = free_agents[:free_agent_limit]
            for player in free_agents:
                add_or_merge(player, drafted=False)
        except Exception:
            print("Could not fetch free agents")

        insert_players(list(players.values()))
        print(f"Inserted {len(players)} players from ESPN league into MongoDB.")

    except Exception as e:
        print(f"Error fetching ESPN data: {e}")
        print("For private leagues, you may need to set ESPN_S2 and SWID in your .env file")

# Example usage:
if __name__ == "__main__":
    populate_from_espn('1004124703')
