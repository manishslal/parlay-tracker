from flask import Blueprint, jsonify, request
from flask_login import login_required
from services import compute_and_persist_returns

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/compute_returns', methods=['POST'])
@login_required
def admin_compute_returns():
	try:
		from flask_login import current_user
		
		if not current_user.is_admin() and current_user.id != 1:
			return jsonify({"error": "Admin access required"}), 403
		
		body = request.get_json() or {}
		force = bool(body.get('force', False))
		results = compute_and_persist_returns(force=force)
		return jsonify(results)
	except Exception as e:
		return jsonify({"error": str(e)}), 500

@admin_bp.route('/admin/fix_pending_legs', methods=['POST'])
@login_required
def admin_fix_pending_legs():
	try:
		from flask_login import current_user
		
		if not current_user.is_admin() and current_user.id != 1:
			return jsonify({"error": "Admin access required"}), 403
		
		# TODO: Move logic from old routes.py/app.py here
		return jsonify({})
	except Exception as e:
		return jsonify({"error": str(e)}), 500

@admin_bp.route('/admin/normalize_team_names', methods=['POST'])
@login_required
def admin_normalize_team_names():
	try:
		from flask_login import current_user
		
		if not current_user.is_admin() and current_user.id != 1:
			return jsonify({"error": "Admin access required"}), 403
		
		# TODO: Move logic from old routes.py/app.py here
		return jsonify({})
	except Exception as e:
		return jsonify({"error": str(e)}), 500

@admin_bp.route('/admin/update_teams', methods=['POST'])
@login_required
def admin_update_teams():
	try:
		from flask_login import current_user
		
		if not current_user.is_admin() and current_user.id != 1:
			return jsonify({"error": "Admin access required"}), 403
		
		# TODO: Move logic from old routes.py/app.py here
		return jsonify({})
	except Exception as e:
		return jsonify({"error": str(e)}), 500

@admin_bp.route('/admin/move_completed', methods=['POST'])
@login_required
def admin_move_completed():
	try:
		from flask_login import current_user
		
		if not current_user.is_admin() and current_user.id != 1:
			return jsonify({"error": "Admin access required"}), 403
		
		# TODO: Move logic from old routes.py/app.py here
		return jsonify({})
	except Exception as e:
		return jsonify({"error": str(e)}), 500

@admin_bp.route('/admin/export_files', methods=['GET'])
@login_required
def admin_export_files():
	try:
		from flask_login import current_user
		
		if not current_user.is_admin() and current_user.id != 1:
			return jsonify({"error": "Admin access required"}), 403
		
		# TODO: Move logic from old routes.py/app.py here
		return jsonify({})
	except Exception as e:
		return jsonify({"error": str(e)}), 500

@admin_bp.route('/admin/process_historical_bets', methods=['POST'])
@login_required
def admin_process_historical_bets():
	try:
		from flask_login import current_user
		
		if not current_user.is_admin() and current_user.id != 1:
			return jsonify({"error": "Admin access required"}), 403
		
		from automation.historical_bet_processing import process_historical_bets_api
		
		# Process historical bets
		process_historical_bets_api()
		
		return jsonify({
			"success": True,
			"message": "Historical bet processing completed successfully"
		})
	except Exception as e:
		return jsonify({"error": str(e)}), 500
