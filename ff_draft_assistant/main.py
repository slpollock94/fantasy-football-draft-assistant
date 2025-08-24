
import os

from .pdf_parser import PDFPlayerSheet
from .openai_parser import parse_table_with_openai
import pdfplumber
from .mongo_utils import insert_players, search_players, get_all_players

def extract_pdf_text(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def main():
    pdf_path = os.path.join(os.path.dirname(__file__), '..', 'Top_300_Full_PPR.pdf')
    json_path = os.path.join(os.path.dirname(__file__), 'parsed_players.json')

    # Option: Use OpenAI to parse columns/tables
    use_openai = True
    columns = ["rank", "name", "position", "team"]

    if use_openai:
        print("Parsing PDF with OpenAI for column/table extraction...")
        text = extract_pdf_text(pdf_path)
        try:
            player_dicts = parse_table_with_openai(text, columns)
            # Save as JSON
            import json
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(player_dicts, f, indent=2)
            print(f"Parsed player data saved to {json_path}")
            # Insert into MongoDB
            insert_players(player_dicts)
            print("Inserted player data into MongoDB.")
            # Print first 10 players from MongoDB
            all_players = get_all_players()
            print("First 10 players from MongoDB:")
            for p in all_players[:10]:
                print(f"{p['rank']}. {p['name']} {p['position']} {p['team']}")
            # Example search: all RBs
            rbs = search_players({"position": "RB"})
            print(f"\nFound {len(rbs)} RBs. Example: {rbs[:3]}")
        except Exception as e:
            print(f"OpenAI parsing failed: {e}")
    else:
        # Fallback: Use standard parser
        sheet = PDFPlayerSheet(pdf_path)
        sheet.parse_pdf()
        sheet.save(json_path)
        print(f"Parsed player data saved to {json_path}")
        # Load player data and show available players
        sheet.load(json_path)
        available = sheet.get_available_players()
        print(f"Available players: {len(available)}")
        for p in available[:10]:
            print(f"{p.rank}. {p.name} {p.position} {p.team}")

    # Example: Mark a player as drafted (for standard parser only)
    # sheet.mark_drafted('Christian McCaffrey')
    # sheet.save(json_path)

if __name__ == "__main__":
    main()
