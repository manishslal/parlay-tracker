from flask import Blueprint, jsonify, request
from flask_login import login_required
from services import compute_and_persist_returns

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/compute_returns', methods=['POST'])
@login_required
def admin_compute_returns():
	try:
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
		# TODO: Move logic from old routes.py/app.py here
		return jsonify({})
	except Exception as e:
		return jsonify({"error": str(e)}), 500

@admin_bp.route('/admin/normalize_team_names', methods=['POST'])
@login_required
def admin_normalize_team_names():
	try:
		# TODO: Move logic from old routes.py/app.py here
		return jsonify({})
	except Exception as e:
		return jsonify({"error": str(e)}), 500

@admin_bp.route('/admin/update_teams', methods=['POST'])
@login_required
def admin_update_teams():
	try:
		# TODO: Move logic from old routes.py/app.py here
		return jsonify({})
	except Exception as e:
		return jsonify({"error": str(e)}), 500

@admin_bp.route('/admin/move_completed', methods=['POST'])
@login_required
def admin_move_completed():
	try:
		# TODO: Move logic from old routes.py/app.py here
		return jsonify({})
	except Exception as e:
		return jsonify({"error": str(e)}), 500

@admin_bp.route('/admin/export_files', methods=['GET'])
@login_required
def admin_export_files():
	try:
		# TODO: Move logic from old routes.py/app.py here
		return jsonify({})
	except Exception as e:
		return jsonify({"error": str(e)}), 500

@admin_bp.route('/admin/backfill_betting_site_id', methods=['POST'])
@login_required
def admin_backfill_betting_site_id():
	try:
		from models import db, Bet
		from flask_login import current_user
		
		if not current_user.is_admin():
			return jsonify({"error": "Admin access required"}), 403
		
		# Get all bets that don't have betting_site_id set
		bets_to_update = Bet.query.filter(
			db.or_(
				Bet.betting_site_id.is_(None),
				Bet.betting_site_id == ''
			)
		).all()
		
		updated_count = 0
		for bet in bets_to_update:
			bet_data = bet.get_bet_data()
			bet_id = bet_data.get('bet_id') or bet_data.get('betting_site_id')
			
			if bet_id:
				bet.betting_site_id = bet_id
				updated_count += 1
		
		if updated_count > 0:
			db.session.commit()
		
		return jsonify({
			"message": f"Backfilled betting_site_id for {updated_count} bets",
			"total_processed": len(bets_to_update)
		})
	except Exception as e:
		return jsonify({"error": str(e)}), 500
