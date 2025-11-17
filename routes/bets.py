from flask import Blueprint, jsonify, request, session
from typing import Any
from flask_login import login_required, current_user
from models import db, Bet
from services import get_user_bets_query, process_parlay_data, has_complete_final_data, save_final_results_to_bet, auto_move_completed_bets, sort_parlays_by_date

bets_bp = Blueprint('bets', __name__)

# API Endpoints

@bets_bp.route('/api/bets', methods=['POST'])
@login_required
def create_bet() -> Any:
	try:
		# ...existing code...
		return jsonify({})
	except Exception as e:
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
def get_current_user() -> Any:
	try:
		# ...existing code...
		return jsonify({})
	except Exception as e:
		return jsonify({"error": str(e)}), 500

@bets_bp.route('/api/users', methods=['GET'])
@login_required
def get_users() -> Any:
	try:
		# ...existing code...
		return jsonify({})
	except Exception as e:
		return jsonify({"error": str(e)}), 500

# Page Routes

@bets_bp.route("/live")
@login_required
def live():
	bets = get_user_bets_query(current_user, is_active=True, is_archived=False, status='live').all()
	live_parlays = [bet.to_dict_structured(use_live_data=True) for bet in bets]
	processed = process_parlay_data(live_parlays)
	return jsonify(sort_parlays_by_date(processed))

@bets_bp.route("/todays")
@login_required
def todays():
	auto_move_completed_bets(current_user.id)
	bets = get_user_bets_query(current_user, is_active=True, is_archived=False, status='pending').all()
	todays_parlays = [bet.to_dict_structured(use_live_data=True) for bet in bets]
	processed = process_parlay_data(todays_parlays)
	return jsonify(sort_parlays_by_date(processed))

@bets_bp.route("/historical")
@login_required
def historical():
	try:
		bets = get_user_bets_query(current_user, is_active=False, is_archived=False).all()
		historical_parlays = [bet.to_dict_structured(use_live_data=False) for bet in bets]
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
def stats():
	auto_move_completed_bets(current_user.id)
	pending_bets = get_user_bets_query(current_user, status_filter='pending').all()
	parlays = [bet.get_bet_data() for bet in pending_bets]
	processed_parlays = process_parlay_data(parlays)
	live_bets = get_user_bets_query(current_user, status_filter='live').all()
	live_parlays = [bet.get_bet_data() for bet in live_bets]
	processed_live = process_parlay_data(live_parlays)
	return jsonify(sort_parlays_by_date(processed_live))
from flask import Blueprint

bets_bp = Blueprint('bets', __name__)

# Add bet-related routes here
