# Fantasy Football Draft Assistant

A Python-based draft assistant that helps you make informed decisions during fantasy football drafts by parsing player rankings, connecting to fantasy APIs, and providing real-time recommendations.

## Features

- **PDF Parsing**: Extract player rankings from PDF sheets using OpenAI for intelligent column detection
- **MongoDB Integration**: Store and search player data with full CRUD operations
- **Web Interface**: Clean, responsive web UI for managing players and draft decisions
- **API Integrations**: Support for Sleeper and ESPN fantasy platforms
- **Real-time Search**: Filter players by position, team, draft status, and more

## Setup

### Prerequisites
- Python 3.13+
- MongoDB Atlas account (or local MongoDB instance)
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd ff_draft_assistant
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
Create a `.env` file in the project root:
```
OPENAI_API_KEY=your_openai_api_key
MONGO_URI=your_mongodb_connection_string
MONGO_DB=fantasyfootball
MONGO_COLLECTION=players
ESPN_S2=your_espn_s2_cookie
SWID=your_swid_cookie
```

### Usage

1. **Parse PDF Rankings** (Optional):
```bash
python main.py
```

2. **Start the Web Application**:
```bash
python app.py
```

3. **Access the Web Interface**:
Open your browser to `http://localhost:4000`

## Project Structure

```
ff_draft_assistant/
├── app.py                 # Flask web application
├── main.py               # PDF parsing and data setup
├── pdf_parser.py         # PDF parsing utilities
├── openai_parser.py      # OpenAI-powered table extraction
├── mongo_utils.py        # MongoDB operations
├── sleeper_api.py        # Sleeper API integration
├── espn_api.py          # ESPN API integration
├── populate_espn.py      # ESPN data population script
├── draft_assistant.py    # Core draft logic
├── templates/
│   └── index.html       # Web interface template
├── requirements.txt      # Python dependencies
├── .env                 # Environment variables (not in repo)
└── .gitignore           # Git ignore rules
```

## API Endpoints

- `GET /` - Web interface
- `GET /api/players` - Get all players (supports filtering by position, team, drafted status)
- `POST /api/populate-espn` - Load data from ESPN league

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License
