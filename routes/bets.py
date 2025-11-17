from flask import Blueprint, jsonify, request, session
from typing import Any
from flask_login import login_required, current_user
from models import db, Bet
from services import get_user_bets_query, process_parlay_data, sort_parlays_by_date
from helpers.database import has_complete_final_data, save_final_results_to_bet, auto_move_completed_bets
from functools import wraps
import logging

bets_bp = Blueprint('bets', __name__)
logger = logging.getLogger(__name__)

def db_error_handler(f):
    """Decorator to handle database connection errors gracefully."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            error_msg = str(e).lower()
            if 'timeout' in error_msg or 'connection' in error_msg or 'ssl' in error_msg:
                # Return a user-friendly error response
                return jsonify({
                    'error': 'Database temporarily unavailable. Please try again in a moment.',
                    'details': 'Connection timeout - this is usually temporary'
                }), 503
            else:
                # Re-raise other errors
                raise
    return wrapper

# API Endpoints

@bets_bp.route('/api/bets', methods=['POST'])
@login_required
def create_bet() -> Any:
	try:
		data = request.get_json()
		if not data:
			return jsonify({"error": "No data provided"}), 400
		
		# Standardize bet type values to match API format
		bet_type_mapping = {
			'parlay': 'Parlay',
			'SGP': 'SGP', 
			'single': 'Single Bet',
			'teaser': 'Teaser'
		}
		
		if 'type' in data:
			data['type'] = bet_type_mapping.get(data['type'], data['type'])
		
		# Generate standardized bet name if not provided or if it's generic
		if 'name' not in data or not data['name'] or data['name'].strip() == '':
			leg_count = len(data.get('legs', []))
			if data['type'] == 'SGP':
				data['name'] = f"{leg_count} Leg SGP"
			elif data['type'] == 'Parlay':
				data['name'] = f"{leg_count} Pick Parlay"
			elif data['type'] == 'Single Bet':
				data['name'] = "Single Bet"
			else:
				data['name'] = f"{leg_count} Pick {data['type']}"
		
		# Ensure status is set properly
		if 'status' not in data:
			data['status'] = 'pending'
		
		# Standardize leg data format
		if 'legs' in data:
			for i, leg in enumerate(data['legs']):
				# Standardize bet_type for legs
				stat = leg.get('stat', '').lower()
				if 'moneyline' in stat:
					leg['bet_type'] = 'moneyline'
				elif 'spread' in stat:
					leg['bet_type'] = 'spread'
				elif 'total' in stat or 'points' in stat:
					leg['bet_type'] = 'total_points'
				else:
					leg['bet_type'] = 'player_prop'
				
				# Ensure required fields are present with correct names
				if 'target_value' not in leg and 'line' in leg:
					leg['target_value'] = leg['line']
				if 'stat_type' not in leg and 'stat' in leg:
					leg['stat_type'] = leg['stat']
				if 'bet_line_type' not in leg and 'stat_add' in leg:
					leg['bet_line_type'] = leg['stat_add']
				
				# Ensure leg_order is set
				if 'leg_order' not in leg:
					leg['leg_order'] = i
		
		# Save bet to database
		from app import save_bet_to_db
		result = save_bet_to_db(current_user.id, data)
		
		return jsonify(result), 201
		
	except Exception as e:
		logger.error(f"Error creating bet: {e}")
		return jsonify({"error": str(e)}), 500

@bets_bp.route('/api/bets/<int:bet_id>', methods=['PUT'])
@login_required
def update_bet(bet_id: int) -> Any:
	try:
		# ...existing code...
		return jsonify({})
	except Exception as e:
		return jsonify({"error": str(e)}), 500

@bets_bp.route('/api/bets/<int:bet_id>', methods=['DELETE'])
@login_required
def delete_bet(bet_id: int) -> Any:
	try:
		# ...existing code...
		return jsonify({})
	except Exception as e:
		return jsonify({"error": str(e)}), 500

@bets_bp.route('/api/bets/<int:bet_id>/archive', methods=['PUT'])
@login_required
def archive_bet(bet_id: int) -> Any:
	try:
		# ...existing code...
		return jsonify({})
	except Exception as e:
		return jsonify({"error": str(e)}), 500

@bets_bp.route('/api/archived', methods=['GET'])
@login_required
def get_archived_bets() -> Any:
	try:
		# ...existing code...
		return jsonify({})
	except Exception as e:
		return jsonify({"error": str(e)}), 500

@bets_bp.route('/api/bets/bulk-archive', methods=['POST'])
@login_required
def bulk_archive_bets() -> Any:
	try:
		# ...existing code...
		return jsonify({})
	except Exception as e:
		return jsonify({"error": str(e)}), 500

@bets_bp.route('/api/bets/bulk-unarchive', methods=['POST'])
@login_required
def bulk_unarchive_bets() -> Any:
	try:
		# ...existing code...
		return jsonify({})
	except Exception as e:
		return jsonify({"error": str(e)}), 500

@bets_bp.route('/api/current_user', methods=['GET'])
@login_required
@db_error_handler
def get_current_user() -> Any:
	try:
		# ...existing code...
		return jsonify({})
	except Exception as e:
		return jsonify({"error": str(e)}), 500

@bets_bp.route('/api/health/db', methods=['GET'])
def db_health_check():
    """Check database connection health."""
    try:
        # Simple query to test connection
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy', 
            'database': 'disconnected',
            'error': str(e)
        }), 503

# Page Routes

@bets_bp.route("/live")
@login_required
@db_error_handler
def live():
	bets = get_user_bets_query(current_user, is_active=True, is_archived=False, status='live').options(db.joinedload(Bet.bet_legs_rel)).all()
	live_parlays = [bet.to_dict_structured(use_live_data=True) for bet in bets]
	processed = process_parlay_data(live_parlays)
	return jsonify(sort_parlays_by_date(processed))

@bets_bp.route("/todays")
@login_required
@db_error_handler
def todays():
	auto_move_completed_bets(current_user.id)
	bets = get_user_bets_query(current_user, is_active=True, is_archived=False, status='pending').options(db.joinedload(Bet.bet_legs_rel)).all()
	todays_parlays = [bet.to_dict_structured(use_live_data=True) for bet in bets]
	processed = process_parlay_data(todays_parlays)
	return jsonify(sort_parlays_by_date(processed))

@bets_bp.route("/historical")
@login_required
@db_error_handler
def historical():
	try:
		bets = get_user_bets_query(current_user, is_active=False, is_archived=False).options(db.joinedload(Bet.bet_legs_rel)).all()
		historical_parlays = []
		for bet in bets:
			parlay = bet.get_bet_data()
			# Add database metadata
			parlay['db_id'] = bet.id
			parlay['user_id'] = bet.user_id
			parlay['bet_type'] = bet.bet_type
			parlay['betting_site'] = bet.betting_site
			parlay['status'] = bet.status
			parlay['is_active'] = bet.is_active
			parlay['is_archived'] = bet.is_archived
			parlay['api_fetched'] = bet.api_fetched
			parlay['created_at'] = bet.created_at
			parlay['updated_at'] = bet.updated_at
			parlay['bet_date'] = bet.bet_date
			historical_parlays.append(parlay)
		if not historical_parlays:
			return jsonify([])
		bets_with_results = []
		bets_needing_live_fetch = []
		bets_needing_initial_fetch = []
		bet_objects = {bet.id: bet for bet in bets}
		for parlay in historical_parlays:
			bet_obj = bet_objects.get(parlay.get('db_id'))
			if bet_obj and bet_obj.api_fetched == 'No':
				bets_needing_live_fetch.append(parlay)
				continue
			if has_complete_final_data(parlay):
				bets_with_results.append(parlay)
			else:
				bets_needing_initial_fetch.append(parlay)
		processed = []
		bets_to_fetch = bets_needing_live_fetch + bets_needing_initial_fetch
		if bets_to_fetch:
			processed = process_parlay_data(bets_to_fetch)
			for parlay in processed:
				bet_obj = bet_objects.get(parlay.get('db_id'))
				if bet_obj:
					is_live_fetch = bet_obj.api_fetched == 'No'
					if is_live_fetch:
						all_finished = all(game.get('statusTypeName') == 'STATUS_FINAL' for game in parlay.get('games', []))
						if all_finished:
							save_final_results_to_bet(bet_obj, [parlay])
							bet_obj.api_fetched = 'Yes'
							bet_obj.status = 'completed'
					else:
						save_final_results_to_bet(bet_obj, [parlay])
						bet_obj.api_fetched = 'Yes'
			db.session.commit()
		processed_with_results = []
		for parlay in bets_with_results:
			if 'games' not in parlay:
				parlay['games'] = []
			processed_with_results.append(parlay)
		all_historical = processed_with_results + processed
		return jsonify(sort_parlays_by_date(all_historical))
	except Exception as e:
		return jsonify({"error": str(e)}), 500

@bets_bp.route("/stats")
@login_required
@db_error_handler
def stats():
	auto_move_completed_bets(current_user.id)
	pending_bets = get_user_bets_query(current_user, status='pending').options(db.joinedload(Bet.bet_legs_rel)).all()
	parlays = [bet.get_bet_data() for bet in pending_bets]
	processed_parlays = process_parlay_data(parlays)
	live_bets = get_user_bets_query(current_user, status='live').options(db.joinedload(Bet.bet_legs_rel)).all()
	live_parlays = [bet.get_bet_data() for bet in live_bets]
	processed_live = process_parlay_data(live_parlays)
	return jsonify(sort_parlays_by_date(processed_live))
