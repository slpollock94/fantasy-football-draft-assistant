from flask import Flask, render_template, request, jsonify
from mongo_utils import get_all_players, search_players, update_player_drafted_status
from populate_espn import populate_from_espn
from player_search import PlayerSearchEngine, quick_search, position_search, format_player_display
from nfl_database import NFLPlayerDatabase, create_mock_comprehensive_database
from nfl_stats_api import NFLStatsAPI
from dotenv import load_dotenv
import logging
import os
import json
import math
from datetime import datetime

app = Flask(__name__)
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize search engine and stats API
search_engine = PlayerSearchEngine()
stats_api = NFLStatsAPI()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/players')
def api_players():
    """Enhanced players endpoint with pagination"""
    position = request.args.get('position')
    team = request.args.get('team')
    drafted = request.args.get('drafted')
    query = request.args.get('query', '')
    
    # Pagination parameters
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    sort_by = request.args.get('sort_by', 'projected_points')
    
    # Use new search engine
    available_only = drafted != 'true' if drafted else True
    
    # Get all matching players first
    all_players = search_engine.search_players(
        query=query,
        position=position,
        team=team,
        max_results=1000,  # Get more to paginate
        sort_by=sort_by,
        available_only=available_only
    )
    
    # Calculate pagination
    total_players = len(all_players)
    total_pages = math.ceil(total_players / per_page)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    # Get players for current page
    players_page = all_players[start_idx:end_idx]
    formatted_players = [format_player_display(player) for player in players_page]
    
    return jsonify({
        'players': formatted_players,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total_players,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1,
            'next_page': page + 1 if page < total_pages else None,
            'prev_page': page - 1 if page > 1 else None
        },
        'query': query,
        'filters': {
            'position': position,
            'team': team,
            'available_only': available_only
        }
    })

@app.route('/api/search')
def api_search():
    """Enhanced player search endpoint"""
    query = request.args.get('q', '')
    position = request.args.get('position', '')
    team = request.args.get('team', '')
    limit = int(request.args.get('limit', 20))
    sort_by = request.args.get('sort_by', 'projected_points')
    available_only = request.args.get('available_only', 'true').lower() == 'true'
    
    players = search_engine.search_players(
        query=query,
        position=position,
        team=team,
        max_results=limit,
        sort_by=sort_by,
        available_only=available_only
    )
    
    formatted_players = [format_player_display(player) for player in players]
    return jsonify({
        'players': formatted_players,
        'total': len(formatted_players),
        'query': query,
        'filters': {
            'position': position,
            'team': team,
            'available_only': available_only
        }
    })

@app.route('/api/position/<position>')
def api_position_search(position):
    """Get top players by position"""
    limit = int(request.args.get('limit', 20))
    available_only = request.args.get('available_only', 'true').lower() == 'true'
    
    if available_only:
        players = search_engine.get_top_players_by_position(position.upper(), limit)
    else:
        players = search_engine.search_players(
            position=position.upper(),
            max_results=limit,
            available_only=False
        )
    
    formatted_players = [format_player_display(player) for player in players]
    return jsonify({
        'players': formatted_players,
        'position': position.upper(),
        'total': len(formatted_players)
    })

@app.route('/api/sleepers')
def api_sleepers():
    """Get sleeper pick recommendations"""
    sleepers = search_engine.get_sleeper_picks()
    formatted_sleepers = [format_player_display(player) for player in sleepers]
    return jsonify({
        'sleepers': formatted_sleepers,
        'total': len(formatted_sleepers)
    })

@app.route('/api/value-picks')
def api_value_picks():
    """Get value pick recommendations"""
    round_num = int(request.args.get('round', 5))
    value_picks = search_engine.get_value_picks(round_num)
    formatted_picks = [format_player_display(player) for player in value_picks]
    return jsonify({
        'value_picks': formatted_picks,
        'total': len(formatted_picks),
        'round': round_num
    })

@app.route('/api/handcuffs/<player_name>')
def api_handcuffs(player_name):
    """Get handcuff suggestions for a player"""
    handcuffs = search_engine.get_handcuff_suggestions(player_name)
    formatted_handcuffs = [format_player_display(player) for player in handcuffs]
    return jsonify({
        'handcuffs': formatted_handcuffs,
        'player': player_name,
        'total': len(formatted_handcuffs)
    })

@app.route('/api/team-analysis', methods=['POST'])
def api_team_analysis():
    """Analyze team composition and needs"""
    data = request.get_json() or {}
    drafted_players = data.get('drafted_players', [])
    
    analysis = search_engine.analyze_team_needs(drafted_players)
    return jsonify(analysis)

@app.route('/api/draft-player', methods=['POST'])
def api_draft_player():
    """Mark a player as drafted"""
    data = request.get_json() or {}
    player_name = data.get('player_name')
    
    if not player_name:
        return jsonify({'success': False, 'error': 'player_name is required'}), 400
    
    try:
        # Update in database
        success = update_player_drafted_status(player_name, True)
        if success:
            # Refresh search engine cache
            search_engine.refresh_cache()
            return jsonify({'success': True, 'message': f'Player {player_name} marked as drafted'})
        else:
            return jsonify({'success': False, 'error': 'Player not found or update failed'}), 404
    except Exception as e:
        logger.exception('Failed to mark player as drafted')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/undraft-player', methods=['POST'])
def api_undraft_player():
    """Mark a player as undrafted (undo draft)"""
    data = request.get_json() or {}
    player_name = data.get('player_name')
    
    if not player_name:
        return jsonify({'success': False, 'error': 'player_name is required'}), 400
    
    try:
        # Update in database
        success = update_player_drafted_status(player_name, False)
        if success:
            # Refresh search engine cache
            search_engine.refresh_cache()
            return jsonify({'success': True, 'message': f'Player {player_name} marked as undrafted'})
        else:
            return jsonify({'success': False, 'error': 'Player not found or update failed'}), 404
    except Exception as e:
        logger.exception('Failed to mark player as undrafted')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/summary')
def api_summary():
    """Get database summary and statistics"""
    summary = search_engine.search_summary()
    return jsonify(summary)

@app.route('/api/populate-espn', methods=['POST'])
def api_populate_espn():
    """Populate data from ESPN league"""
    data = request.get_json(silent=True) or {}
    league_id = data.get('league_id') or os.getenv('ESPN_LEAGUE_ID')
    year = data.get('year') or os.getenv('ESPN_YEAR')

    if not league_id:
        logger.error('League ID not provided')
        return jsonify({'success': False, 'error': 'league_id is required'}), 400

    try:
        year = int(year) if year is not None else datetime.now().year
    except (TypeError, ValueError):
        logger.warning('Invalid year provided: %s; defaulting to current year', year)
        year = datetime.now().year

    try:
        populate_from_espn(league_id, year=year)
        search_engine.refresh_cache()  # Refresh after population
        logger.info('Successfully populated data from ESPN league %s for year %s', league_id, year)
        return jsonify({'success': True, 'message': f'Populated data from ESPN league {league_id}'})
    except Exception as e:
        logger.exception('Failed to populate ESPN data')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/player/<player_name>')
def api_player_detail(player_name):
    """Get detailed player information including historical stats"""
    try:
        # Search for the player
        players = search_engine.search_players(query=player_name, max_results=5)
        
        if not players:
            return jsonify({'error': 'Player not found'}), 404
        
        # Find exact match or closest match
        player = None
        for p in players:
            if p.get('name', '').lower() == player_name.lower():
                player = p
                break
        
        if not player:
            player = players[0]  # Use first result if no exact match
        
        # Get basic player info
        player_info = {
            'name': player.get('name'),
            'position': player.get('position'),
            'team': player.get('team'),
            'adp': player.get('adp'),
            'projected_points': player.get('projected_points'),
            'rank': player.get('rank'),
            'drafted': player.get('drafted', False)
        }
        
        # Get historical stats
        try:
            career_stats = stats_api.get_player_career_stats(
                player['name'], 
                player['position']
            )
            player_info['career_stats'] = career_stats
        except Exception as e:
            logger.warning(f"Could not fetch career stats for {player['name']}: {e}")
            player_info['career_stats'] = {}
        
        # Get current year projections
        try:
            projections = stats_api.get_player_projections(
                player['name'], 
                player['position']
            )
            player_info['projections'] = projections
        except Exception as e:
            logger.warning(f"Could not fetch projections for {player['name']}: {e}")
            player_info['projections'] = {}
        
        # Get similar players / recommendations
        similar_players = search_engine.search_players(
            position=player['position'],
            team=player['team'],
            max_results=5,
            available_only=True
        )
        
        # Remove the current player from similar players
        similar_players = [p for p in similar_players if p.get('name') != player['name']][:3]
        
        player_info['similar_players'] = [format_player_display(p) for p in similar_players]
        
        return jsonify({
            'success': True,
            'player': player_info,
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.exception(f'Error fetching player details for {player_name}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/populate-nfl', methods=['POST'])
def api_populate_nfl():
    """Populate comprehensive NFL player database"""
    data = request.get_json(silent=True) or {}
    max_players = data.get('max_players', 500)
    use_mock = data.get('use_mock', False)
    
    try:
        if use_mock:
            logger.info('Populating with comprehensive mock NFL database...')
            mock_players = create_mock_comprehensive_database()
            from mongo_utils import insert_players
            insert_players(mock_players)
            
            message = f'Successfully populated {len(mock_players)} mock NFL players'
            logger.info(message)
        else:
            logger.info('Populating with real NFL data from Sleeper API...')
            nfl_db = NFLPlayerDatabase()
            success = nfl_db.populate_database(max_players=max_players)
            
            if not success:
                # Fallback to mock data
                logger.info('Falling back to mock data...')
                mock_players = create_mock_comprehensive_database()
                from mongo_utils import insert_players
                insert_players(mock_players)
                message = f'API failed, populated {len(mock_players)} mock NFL players'
            else:
                message = f'Successfully populated NFL database with up to {max_players} players'
        
        # Refresh search engine cache
        search_engine.refresh_cache()
        
        return jsonify({
            'success': True, 
            'message': message,
            'summary': search_engine.search_summary()
        })
        
    except Exception as e:
        logger.exception('Failed to populate NFL database')
        return jsonify({'success': False, 'error': str(e)}), 500

# Initialize search engine cache on startup (removed deprecated before_first_request)
try:
    search_engine.refresh_cache()
    logger.info('Search engine initialized successfully')
except Exception as e:
    logger.warning(f'Failed to initialize search engine: {e}')

if __name__ == '__main__':
    app.run(debug=True, port=4000)
