from flask import Flask, render_template, request, jsonify
from .mongo_utils import get_all_players, search_players
from .populate_espn import populate_from_espn
from dotenv import load_dotenv
import logging
import os

app = Flask(__name__)
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/players')
def api_players():
    position = request.args.get('position')
    team = request.args.get('team')
    drafted = request.args.get('drafted')
    query = {}
    if position:
        query['position'] = position
    if team:
        query['team'] = team.upper()
    if drafted:
        query['drafted'] = drafted.lower() == 'true'
    if query:
        players = search_players(query)
    else:
        players = get_all_players()
    return jsonify(players)

@app.route('/api/populate-espn', methods=['POST'])
def api_populate_espn():
    data = request.get_json(silent=True) or {}
    league_id = data.get('league_id') or os.getenv('ESPN_LEAGUE_ID')

    if not league_id:
        logger.error('League ID not provided')
        return jsonify({'success': False, 'error': 'league_id is required'}), 400

    try:
        populate_from_espn(league_id)
        logger.info('Successfully populated data from ESPN league %s', league_id)
        return jsonify({'success': True})
    except Exception as e:
        logger.exception('Failed to populate ESPN data')
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=4000)
