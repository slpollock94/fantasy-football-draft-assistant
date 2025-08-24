# AGENTS.md


## Project Overview
This project is a Python-based package designed to assist users during fantasy football drafts. It will:

- Accept a user-provided PDF sheet as a starting point for rankings.
- Parse the PDF to extract player rankings and relevant data, including support for multi-column/tabular formats.
- Use LLMs (such as Llama 2 or OpenAI GPT) to help interpret and structure complex or inconsistent PDF data.
- Connect to the Sleeper API (and ESPN if possible) to:
  - Pull results of completed drafts.
  - Analyze the average draft position (ADP) of players.
- Provide real-time suggestions for who to draft next based on:
  - The user's sheet.
  - Live draft results.
  - ADP and other relevant data.

## Agent Instructions
- Maintain this document as the central source of project requirements and agent instructions.
- All code should be written in Python.
- Prioritize modular, testable, and well-documented code.
- Use popular libraries for PDF parsing (e.g., PyPDF2, pdfplumber) and HTTP requests (e.g., requests).
- Integrate LLMs (Llama 2, OpenAI GPT, etc.) for advanced parsing of tabular or complex PDF data.
- Keep all API keys and secrets (e.g., OpenAI key) in environment variables, loaded from a `.env` file, and ensure `.env` is listed in `.gitignore`.
- Ensure extensibility for supporting additional fantasy platforms (e.g., ESPN).
- Provide clear interfaces for inputting the user's sheet and connecting to APIs.
- Implement robust error handling and logging.
- Update this document as requirements evolve or new features are added.

## Next Steps
1. Set up the Python project structure.
2. Implement PDF parsing functionality, including LLM-based column/table extraction.
3. Integrate with the Sleeper API (and ESPN if feasible).
4. Add OpenAI (or Llama 2) integration for advanced parsing.
5. Store all API keys in a `.env` file and keep it out of version control.
6. Develop logic for real-time draft recommendations.
7. Add CLI or web interface for user interaction.
8. Write tests and documentation.
