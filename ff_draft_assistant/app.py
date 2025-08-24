from flask import Flask, render_template, request, jsonify
from mongo_utils import get_all_players, search_players
# from populate_espn import populate_from_espn
import os

app = Flask(__name__)

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
    # Temporarily disabled due to import issues
    return jsonify({'success': False, 'error': 'ESPN integration temporarily disabled'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=4000)
