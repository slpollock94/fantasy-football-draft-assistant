from ff_draft_assistant.draft_assistant import DraftAssistant
import os

def main():
    pdf_path = os.path.join(os.path.dirname(__file__), '..', 'Top_300_Full_PPR.pdf')
    json_path = os.path.join(os.path.dirname(__file__), 'parsed_players.json')
    assistant = DraftAssistant(pdf_path, json_path)

    print("Top 5 available players:")
    for p in assistant.get_next_best():
        print(f"{p.rank}. {p.name} {p.position} {p.team}")

    # Example: Mark a player as drafted
    # assistant.mark_player_drafted('Christian McCaffrey')
    # print("Player marked as drafted.")

    # Example: Get Sleeper ADP data (raw)
    # adp = assistant.get_sleeper_adp()
    # print(adp)

if __name__ == "__main__":
    main()
