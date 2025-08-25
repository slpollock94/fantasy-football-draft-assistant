import pdfplumber
import json
import re
import logging
from typing import List, Dict, Optional
from player_validator import PlayerDataValidator

logger = logging.getLogger(__name__)

class Player:
    def __init__(self, name: str, position: str, team: str, rank: int, adp: Optional[float] = None):
        self.name = name
        self.position = position
        self.team = team
        self.rank = rank
        self.drafted = False
        self.adp = adp

    def to_dict(self):
        return {
            'name': self.name,
            'position': self.position,
            'team': self.team,
            'rank': self.rank,
            'drafted': self.drafted,
            'adp': self.adp
        }

    @staticmethod
    def from_dict(data):
        p = Player(data['name'], data['position'], data['team'], data['rank'], data.get('adp'))
        p.drafted = data.get('drafted', False)
        return p

class EnhancedPDFParser:
    """Enhanced PDF parser with better validation and multiple format support"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.players: List[Dict] = []
        self.validator = PlayerDataValidator()
        
        # Multiple parsing patterns for different PDF formats
        self.patterns = [
            # Pattern 1: "1. Christian McCaffrey RB SF 1.2"
            r'(\d+)\.?\s+([A-Za-z\s\.\']+?)\s+([A-Z]{1,3})\s+([A-Z]{2,4})(?:\s+(\d+(?:\.\d+)?))?',
            # Pattern 2: "1 Christian McCaffrey, RB, SF, 1.2"
            r'(\d+)\s+([A-Za-z\s\.\']+?),\s*([A-Z]{1,3}),\s*([A-Z]{2,4})(?:,\s*(\d+(?:\.\d+)?))?',
            # Pattern 3: "Christian McCaffrey (RB - SF) - 1.2"
            r'([A-Za-z\s\.\']+?)\s*\(([A-Z]{1,3})\s*-\s*([A-Z]{2,4})\)\s*-?\s*(\d+(?:\.\d+)?)?',
            # Pattern 4: Table format "1 | Christian McCaffrey | RB | SF | 1.2"
            r'(\d+)\s*\|\s*([A-Za-z\s\.\']+?)\s*\|\s*([A-Z]{1,3})\s*\|\s*([A-Z]{2,4})(?:\s*\|\s*(\d+(?:\.\d+)?))?',
            # Pattern 5: Rank at end "Christian McCaffrey RB SF 1"
            r'([A-Za-z\s\.\']+?)\s+([A-Z]{1,3})\s+([A-Z]{2,4})\s+(\d+)$'
        ]
    
    def parse_pdf(self) -> List[Dict]:
        """Parse PDF using multiple strategies"""
        logger.info(f"Starting PDF parsing for {self.pdf_path}")
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    logger.debug(f"Processing page {page_num}")
                    
                    # Try table extraction first
                    tables = page.extract_tables()
                    if tables:
                        self._parse_tables(tables)
                    
                    # Extract text and parse
                    text = page.extract_text()
                    if text:
                        self._parse_text_enhanced(text)
            
            # Validate and clean extracted data
            self._validate_and_clean()
            
            logger.info(f"PDF parsing complete: extracted {len(self.players)} valid players")
            return self.players
            
        except Exception as e:
            logger.error(f"Error parsing PDF {self.pdf_path}: {e}")
            return []
    
    def _parse_tables(self, tables: List[List[List[str]]]):
        """Parse table-based data"""
        for table in tables:
            if not table or len(table) < 2:
                continue
                
            # Skip header row
            for row in table[1:]:
                if not row or len(row) < 3:
                    continue
                    
                try:
                    # Flexible table parsing
                    player_data = self._extract_player_from_row(row)
                    if player_data:
                        self.players.append(player_data)
                except Exception as e:
                    logger.debug(f"Error parsing table row {row}: {e}")
                    continue
    
    def _extract_player_from_row(self, row: List[str]) -> Optional[Dict]:
        """Extract player data from table row"""
        # Clean row data
        clean_row = [cell.strip() if cell else '' for cell in row]
        
        # Try different column arrangements
        arrangements = [
            # [rank, name, position, team, adp]
            {'rank': 0, 'name': 1, 'position': 2, 'team': 3, 'adp': 4},
            # [name, position, team, adp]
            {'name': 0, 'position': 1, 'team': 2, 'adp': 3},
            # [rank, name, position, team]
            {'rank': 0, 'name': 1, 'position': 2, 'team': 3}
        ]
        
        for arrangement in arrangements:
            try:
                player_data = {}
                
                # Extract rank
                if 'rank' in arrangement and len(clean_row) > arrangement['rank']:
                    rank_text = clean_row[arrangement['rank']]
                    player_data['rank'] = self._extract_number(rank_text)
                
                # Extract name
                if len(clean_row) > arrangement['name']:
                    name = clean_row[arrangement['name']]
                    if name and len(name) > 1:
                        player_data['name'] = self.validator.clean_player_name(name)
                
                # Extract position and team
                if len(clean_row) > arrangement['position']:
                    player_data['position'] = self.validator.normalize_position(clean_row[arrangement['position']])
                
                if len(clean_row) > arrangement['team']:
                    player_data['team'] = self.validator.normalize_team(clean_row[arrangement['team']])
                
                # Extract ADP if present
                if 'adp' in arrangement and len(clean_row) > arrangement['adp']:
                    player_data['adp'] = self._extract_number(clean_row[arrangement['adp']])
                
                # Validate basic requirements
                if (player_data.get('name') and 
                    player_data.get('position') and 
                    player_data.get('team')):
                    return player_data
                    
            except Exception:
                continue
        
        return None
    
    def _parse_text_enhanced(self, text: str):
        """Enhanced text parsing with multiple pattern recognition"""
        lines = text.split('\n')
        rank_counter = 1
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:  # Skip very short lines
                continue
            
            # Try each pattern
            for pattern_idx, pattern in enumerate(self.patterns):
                try:
                    match = re.search(pattern, line)
                    if match:
                        player_data = self._process_pattern_match(match, pattern_idx, rank_counter)
                        if player_data:
                            self.players.append(player_data)
                            rank_counter += 1
                            break
                except Exception as e:
                    logger.debug(f"Pattern {pattern_idx} failed on line '{line}': {e}")
                    continue
    
    def _process_pattern_match(self, match, pattern_idx: int, rank_counter: int) -> Optional[Dict]:
        """Process regex match based on pattern type"""
        try:
            groups = match.groups()
            
            if pattern_idx == 0:  # "1. Christian McCaffrey RB SF 1.2"
                rank, name, position, team = groups[:4]
                adp = groups[4] if len(groups) > 4 else None
            elif pattern_idx == 1:  # "1 Christian McCaffrey, RB, SF, 1.2"
                rank, name, position, team = groups[:4]
                adp = groups[4] if len(groups) > 4 else None
            elif pattern_idx == 2:  # "Christian McCaffrey (RB - SF) - 1.2"
                name, position, team = groups[:3]
                adp = groups[3] if len(groups) > 3 else None
                rank = rank_counter
            elif pattern_idx == 3:  # Table format
                rank, name, position, team = groups[:4]
                adp = groups[4] if len(groups) > 4 else None
            elif pattern_idx == 4:  # Rank at end
                name, position, team, rank = groups
                adp = None
            else:
                return None
            
            # Clean and validate data
            clean_name = self.validator.clean_player_name(name)
            clean_position = self.validator.normalize_position(position)
            clean_team = self.validator.normalize_team(team)
            
            if not clean_name or not clean_position or not clean_team:
                return None
            
            player_data = {
                'name': clean_name,
                'position': clean_position,
                'team': clean_team,
                'rank': int(rank) if rank and str(rank).isdigit() else rank_counter,
                'source': 'pdf_parser'
            }
            
            if adp:
                player_data['adp'] = self._extract_number(adp)
            
            return player_data
            
        except Exception as e:
            logger.debug(f"Error processing match: {e}")
            return None
    
    def _extract_number(self, text) -> Optional[float]:
        """Extract numeric values from text"""
        if not text:
            return None
            
        if isinstance(text, (int, float)):
            return float(text)
        
        # Clean text and extract number
        text = str(text).strip()
        match = re.search(r'(\d+(?:\.\d+)?)', text)
        
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        
        return None
    
    def _validate_and_clean(self):
        """Validate and clean extracted player data"""
        if not self.players:
            return
        
        logger.info(f"Validating {len(self.players)} extracted players...")
        
        # Remove duplicates and validate
        validated_players = self.validator.detect_duplicates(self.players)
        
        # Final validation
        final_players = []
        for player in validated_players:
            if self.validator.validate_player_data(player):
                final_players.append(player)
        
        removed_count = len(self.players) - len(final_players)
        logger.info(f"Validation complete: {len(final_players)} valid players, {removed_count} removed")
        
        self.players = final_players
    
    def get_players_dict(self) -> List[Dict]:
        """Return players as dictionary list"""
        return self.players
    
    def save_to_json(self, output_path: str):
        """Save parsed players to JSON file"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.players, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.players)} players to {output_path}")
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")

# Legacy class for backwards compatibility
class PDFPlayerSheet:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.parser = EnhancedPDFParser(pdf_path)
        self.players: List[Player] = []

    def parse_pdf(self):
        """Parse PDF using enhanced parser"""
        player_dicts = self.parser.parse_pdf()
        self.players = [Player.from_dict(p) for p in player_dicts]

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
