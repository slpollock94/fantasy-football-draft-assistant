from ff_draft_assistant.pdf_parser import PDFPlayerSheet
from ff_draft_assistant.sleeper_api import SleeperAPI
from ff_draft_assistant.espn_http_api import ESPNAPI

class DraftAssistant:
    def __init__(self, pdf_path: str, json_path: str):
        self.sheet = PDFPlayerSheet(pdf_path)
        self.json_path = json_path
        self.sheet.parse_pdf()
        self.sheet.save(json_path)
        self.sheet.load(json_path)

    def mark_player_drafted(self, player_name: str):
        self.sheet.mark_drafted(player_name)
        self.sheet.save(self.json_path)

    def get_next_best(self, n=5):
        available = self.sheet.get_available_players()
        return available[:n]

    def get_sleeper_adp(self):
        # Placeholder for ADP logic
        players = SleeperAPI.get_players()
        # ...process ADP...
        return players

    def get_espn_league(self, league_id: str):
        return ESPNAPI.get_league(league_id)

    def get_espn_draft(self, league_id: str):
        return ESPNAPI.get_draft(league_id)

# Example usage:
# assistant = DraftAssistant('Top_300_Full_PPR.pdf', 'parsed_players.json')
# assistant.mark_player_drafted('Christian McCaffrey')
# print(assistant.get_next_best())
