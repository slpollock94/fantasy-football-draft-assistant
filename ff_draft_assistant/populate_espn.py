import os
from datetime import datetime

from dotenv import load_dotenv
from espn_api.football import League
from mongo_utils import insert_players

load_dotenv()


def populate_from_espn(league_id: str, season: int | None = None):
    season = season or datetime.now().year
    # For private leagues, you may need ESPN cookies
    espn_s2 = os.getenv("ESPN_S2")
    swid = os.getenv("SWID")

    try:
        if espn_s2 and swid:
            league = League(
                league_id=league_id, year=season, espn_s2=espn_s2, swid=swid
            )
        else:
            league = League(league_id=league_id, year=season)
        
        players = []
        
        # Get all teams and their rosters
        for team in league.teams:
            for player in team.roster:
                player_data = {
                    'rank': str(getattr(player, 'draft_pick', '')),
                    'name': player.name,
                    'position': player.position,
                    'team': getattr(player, 'proTeam', ''),
                    'projected_points': getattr(player, 'projected_total_points', 0),
                    'avg_points': getattr(player, 'avg_points', 0),
                    'drafted': True
                }
                players.append(player_data)
        
        # Also get free agents if available
        try:
            free_agents = league.free_agents()[:50]  # Get top 50 free agents
            for player in free_agents:
                player_data = {
                    'rank': '',
                    'name': player.name,
                    'position': player.position,
                    'team': getattr(player, 'proTeam', ''),
                    'projected_points': getattr(player, 'projected_total_points', 0),
                    'avg_points': getattr(player, 'avg_points', 0),
                    'drafted': False
                }
                players.append(player_data)
        except:
            print("Could not fetch free agents")
        
        insert_players(players)
        print(f"Inserted {len(players)} players from ESPN league into MongoDB.")
        
    except Exception as e:
        print(f"Error fetching ESPN data: {e}")
        print("For private leagues, you may need to set ESPN_S2 and SWID in your .env file")

# Example usage:
if __name__ == "__main__":
    populate_from_espn('1004124703')
