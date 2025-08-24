import pdfplumber
import json
from typing import List, Dict, Optional

class Player:
    def __init__(self, name: str, position: str, team: str, rank: int):
        self.name = name
        self.position = position
        self.team = team
        self.rank = rank
        self.drafted = False

    def to_dict(self):
        return {
            'name': self.name,
            'position': self.position,
            'team': self.team,
            'rank': self.rank,
            'drafted': self.drafted
        }

    @staticmethod
    def from_dict(data):
        p = Player(data['name'], data['position'], data['team'], data['rank'])
        p.drafted = data.get('drafted', False)
        return p

class PDFPlayerSheet:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.players: List[Player] = []

    def parse_pdf(self):
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    self._parse_text(text)

    def _parse_text(self, text: str):
        # TODO: Adjust this parsing logic to match the PDF format
        lines = text.split('\n')
        for line in lines:
            # Example: "1. Christian McCaffrey RB SF"
            parts = line.strip().split()
            if len(parts) >= 4 and parts[0].replace('.', '').isdigit():
                try:
                    rank = int(parts[0].replace('.', ''))
                    name = ' '.join(parts[1:-2])
                    position = parts[-2]
                    team = parts[-1]
                    self.players.append(Player(name, position, team, rank))
                except Exception:
                    continue

    def save(self, path: str):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump([p.to_dict() for p in self.players], f, indent=2)

    def load(self, path: str):
        with open(path, 'r', encoding='utf-8') as f:
            self.players = [Player.from_dict(d) for d in json.load(f)]

    def mark_drafted(self, player_name: str):
        for p in self.players:
            if p.name.lower() == player_name.lower():
                p.drafted = True
                break

    def get_available_players(self) -> List[Player]:
        return [p for p in self.players if not p.drafted]

# Example usage:
# sheet = PDFPlayerSheet('Top_300_Full_PPR.pdf')
# sheet.parse_pdf()
# sheet.save('parsed_players.json')
# sheet.load('parsed_players.json')
# sheet.mark_drafted('Christian McCaffrey')
# available = sheet.get_available_players()
