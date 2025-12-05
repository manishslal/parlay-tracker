from flask import Blueprint, jsonify, request, session
from typing import Any
from flask_login import login_required, current_user
from models import db, Bet, BetLeg
from services import get_user_bets_query, process_parlay_data, sort_parlays_by_date
from stat_standardization import standardize_stat_type, get_all_stats_for_sport
from helpers.database import has_complete_final_data, save_final_results_to_bet, auto_move_completed_bets, auto_move_pending_to_live
from sqlalchemy import or_
import datetime as dt_module  # Import entire datetime module
import pytz  # For timezone handling
# from app import app  # Removed to avoid circular import
from functools import wraps
import logging
import os
import requests
import json
from werkzeug.utils import secure_filename

bets_bp = Blueprint('bets', __name__)
logger = logging.getLogger(__name__)

# Configuration for file uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_betslip_image(file):
    """Process a bet slip image using OpenAI Vision API."""
    try:
        # Read the file
        file_content = file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise ValueError("File too large. Maximum size is 10MB.")
        
        # Get OpenAI API key from environment
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not configured on server")
        
        # Convert to base64
        import base64
        base64_image = base64.b64encode(file_content).decode('utf-8')
        
        # Determine MIME type
        filename = secure_filename(file.filename).lower()
        if filename.endswith('.png'):
            mime_type = 'image/png'
        elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
            mime_type = 'image/jpeg'
        elif filename.endswith('.gif'):
            mime_type = 'image/gif'
        else:
            mime_type = 'image/jpeg'  # default
        
        # Call OpenAI Vision API
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'gpt-4o',
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': '''Extract betting information from this bet slip image. You are an expert at reading sports betting slips. Return ONLY a valid JSON object with this exact structure. Do not include any markdown formatting, code blocks, or additional text.

CRITICAL INSTRUCTIONS:
- Look for the betting site name (DraftKings, FanDuel, BetMGM, Caesars, etc.)
- Identify the bet type: "parlay" for multiple legs, "single" for one leg, "teaser" for adjusted spreads, "round_robin" for combinations
- Extract the total wager amount and potential payout
- Parse each betting leg carefully - these are the individual bets that make up the parlay/single

FOR EACH LEG, identify:
- Player name (for player props) or team name (for game bets)
- The stat being bet on (points, rebounds, passing yards, total points, spread, moneyline, etc.)
- The betting line (the number, like +4.5, -110, over 45.5, etc.)
- Whether it's over/under for totals, or the direction for spreads
- Individual leg odds if shown separately
- Home and away teams if the matchup is shown (e.g., "LAL @ BOS" or "Lakers vs Celtics")

EXAMPLES of how to parse different bet types:

Moneyline: "Los Angeles Lakers ML" → team: "Los Angeles Lakers", stat: "moneyline", line: 0
Spread: "Boston Celtics -3.5" → team: "Boston Celtics", stat: "spread", line: -3.5
Total: "Game Total Over 220.5" → team: "Game Total", stat: "total_points", line: 220.5, stat_add: "over"
Player Prop: "LeBron James Over 25.5 Points" → player: "LeBron James", team: "Los Angeles Lakers", stat: "points", line: 25.5, stat_add: "over"
SGP with matchup: "LAL @ BOS - LeBron James Over 25.5 Points" → player: "LeBron James", team: "Los Angeles Lakers", away_team: "Los Angeles Lakers", home_team: "Boston Celtics"

{
  "bet_id": "the bet confirmation number visible on the slip (e.g., 'O/0240915/0000074' for FanDuel, 'DK638926171300468480' for DraftKings)",
  "bet_site": "name of the betting site (e.g., DraftKings, FanDuel, Caesars, BetMGM)",
  "bet_type": "parlay|sgp|single|teaser|round_robin (use 'sgp' for Same Game Parlay or Single Game Parlay)",
  "total_odds": "number like +150, -120, or the American odds format",
  "wager_amount": "number like 10.00, 25.50 - the amount being wagered",
  "potential_payout": "number like 35.00 - total amount you'd receive including wager",
  "bet_date": "YYYY-MM-DD format if visible, otherwise omit",
  "legs": [
    {
      "player": "Player name (ONLY for player props, otherwise omit this field)",
      "team": "Team name or 'Game Total' for totals bets",
      "home_team": "Home team name ONLY if matchup shows '@' (e.g., 'LAL @ BOS' means BOS is home). Omit if 'vs' is used or unclear.",
      "away_team": "Away team name ONLY if matchup shows '@' (e.g., 'LAL @ BOS' means LAL is away). Omit if 'vs' is used or unclear.",
      "stat": "stat type: 'moneyline', 'spread', 'total_points', 'passing_yards', 'points', 'rebounds', 'assists', etc.",
      "line": "the betting line as a number: -3.5, +150, 25.5, 220.5, etc.",
      "stat_add": "'over' or 'under' for totals/player props, omit for moneyline/spread",
      "odds": "leg-specific odds if shown (like -110), otherwise omit"
    }
  ]
}

IMPORTANT: 
- Only include fields that are clearly visible in the image
- For team names, use the full name as shown (e.g., "Kansas City Chiefs", not "Chiefs")
- For stats, be specific: "passing_yards" not "passing", "total_points" not "totals"
- If a leg has both player and team, include both fields
- The bet_id is CRITICAL - look for confirmation number, reference number, or bet ID on the slip
- For SGP/Same Game Parlay bets, use bet_type: "sgp"
- For home/away teams: If matchup uses '@' (LAL @ BOS), BOS is home. If 'vs', leave home_team and away_team blank.
- Return ONLY the JSON object, no explanations or additional text.'''
                        },
                        {
                            'type': 'image_url',
                            'image_url': {
                                'url': f'data:{mime_type};base64,{base64_image}'
                            }
                        }
                    ]
                }
            ],
            'max_tokens': 2000  # Increased from 1000 to prevent truncation of multi-leg parlays
        }
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            raise ValueError(f"OpenAI API error: {response.status_code} - {response.text}")
        
        try:
            result = response.json()
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse OpenAI API response as JSON: {e}. Response text: {response.text[:500]}")
        
        # Debug: Log the full response structure
        logger.info(f"OpenAI API response: {result}")
        
        # Validate response structure
        if 'choices' not in result or not result['choices']:
            raise ValueError(f"OpenAI API returned no choices: {result}")
        
        if 'message' not in result['choices'][0]:
            raise ValueError(f"OpenAI API choice has no message: {result['choices'][0]}")
        
        content = result['choices'][0]['message']['content']
        
        # Debug: Log the content before parsing
        logger.info(f"OpenAI content to parse: {content}")
        
        if not content or not content.strip():
            raise ValueError("OpenAI API returned empty content")
        
        # Clean the content - remove markdown code blocks if present
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:]
        if content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        # Parse the JSON response
        try:
            extracted_data = json.loads(content)
        except json.JSONDecodeError as e:
            # Try to extract JSON from the content if it contains extra text
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    extracted_data = json.loads(json_match.group())
                except json.JSONDecodeError:
                    raise ValueError(f"Failed to parse OpenAI response as JSON: {e}. Content: {content[:500]}")
            else:
                raise ValueError(f"Failed to parse OpenAI response as JSON: {e}. Content: {content[:500]}")
        
        # Validate the structure
        if not isinstance(extracted_data, dict):
            raise ValueError("Invalid response format from OpenAI")
        
        # Ensure required fields have defaults
        extracted_data.setdefault('bet_site', 'Unknown')
        extracted_data.setdefault('bet_type', 'parlay')
        extracted_data.setdefault('legs', [])
        
        return extracted_data
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse OpenAI response as JSON: {e}")
    except Exception as e:
        logger.error(f"Error processing bet slip image: {e}")
        raise

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
		
		# FIX: Rename 'type' to 'bet_type' to match save_bet_to_db expectations
		if 'type' in data:
			data['bet_type'] = data.pop('type')
		
		# Generate standardized bet name if not provided or if it's generic
		if 'name' not in data or not data['name'] or data['name'].strip() == '':
			leg_count = len(data.get('legs', []))
			if data.get('bet_type') == 'SGP':
				data['name'] = f"{leg_count} Leg SGP"
			elif data.get('bet_type') == 'Parlay':
				data['name'] = f"{leg_count} Pick Parlay"
			elif data.get('bet_type') == 'Single Bet':
				data['name'] = "Single Bet"
			else:
				data['name'] = f"{leg_count} Pick {data.get('bet_type')}"
		
		# Ensure status is set properly
		if 'status' not in data:
			data['status'] = 'pending'
		
		# Handle secondary bettors
		if 'secondary_bettor_ids' in data and data['secondary_bettor_ids']:
			# Ensure it's a list of integers
			data['secondary_bettor_ids'] = [int(id) for id in data['secondary_bettor_ids'] if id]
		
		# Standardize leg data format
		if 'legs' in data:
			for i, leg in enumerate(data['legs']):
				# Standardize bet_type for legs
				stat = leg.get('stat', '').lower()
				
				# Determine if it's a Team Prop
				is_team_prop = False
				if 'moneyline' in stat:
					leg['stat_type'] = 'moneyline'
					leg['target_value'] = 0.00
					is_team_prop = True
				elif 'spread' in stat:
					leg['stat_type'] = 'spread'
					is_team_prop = True
				elif 'total' in stat or 'points' in stat and leg.get('team') == 'Game Total':
					leg['stat_type'] = 'total_points'
					is_team_prop = True
				elif leg.get('team') == 'Game Total':
					leg['stat_type'] = 'total_points' # Default for Game Total
					is_team_prop = True
				
				# Set bet_type based on classification
				if is_team_prop:
					leg['bet_type'] = 'Team Prop'
				else:
					leg['bet_type'] = 'Player Prop'
					# If stat_type wasn't set above, use the stat field
					if 'stat_type' not in leg:
						leg['stat_type'] = stat
				
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

@bets_bp.route('/api/bets/<int:bet_id>/sport', methods=['PUT'])
@login_required
def correct_sport(bet_id):
    """Task 6: Correct the sport classification for a bet.
    
    Allows users to fix incorrect sport detection. Clears cached game data 
    and resets leg status to force re-fetch from ESPN API.
    
    Request body:
        {
            'sport': 'NBA',  # Required: valid sport (NFL, NBA, MLB, NHL, NCAAF, NCAAB)
            'leg_order': 0   # Optional: specific leg index to update (0-based)
        }
    
    Response:
        {
            'message': 'Sport corrected to NBA',
            'legs_updated': 2,
            'sport': 'NBA'
        }
    """
    bet = Bet.query.get(bet_id)
    if not bet or not current_user.can_access(bet):
        return {'error': 'Bet not found'}, 404
    
    data = request.json or {}
    new_sport = data.get('sport', '').strip().upper()
    
    # Validate sport
    VALID_SPORTS = {'NFL', 'NBA', 'MLB', 'NHL', 'NCAAF', 'NCAAB'}
    if new_sport not in VALID_SPORTS:
        return {'error': f'Invalid sport. Must be one of: {", ".join(VALID_SPORTS)}'}, 400
    
    # Determine which legs to update (all, or specific leg_order)
    leg_order = data.get('leg_order')  # Optional: specific leg to update
    
    # Get all bet legs
    bet_legs = BetLeg.query.filter_by(bet_id=bet_id).all()
    
    updated_count = 0
    for leg in bet_legs:
        # If specific leg_order provided, only update that leg
        if leg_order is not None and leg.leg_order != leg_order:
            continue
        
        # Only update if sport is different
        if leg.sport != new_sport:
            leg.sport = new_sport
            leg.status = 'pending'  # Reset status to force re-fetch
            leg.achieved_value = None  # Clear cached values
            leg.home_score = None
            leg.away_score = None
            leg.current_quarter = None
            leg.time_remaining = None
            updated_count += 1
    
    if updated_count > 0:
        db.session.commit()
        
        # Clear game data cache for this bet (if cache exists)
        # This ensures next live tracking will fetch fresh ESPN data
        cache_key = f"bet_games_{bet_id}"
        try:
            from app import cache
            cache.delete(cache_key)
        except Exception:
            pass  # Cache not available, will be cleared naturally
        
        logger.info(f"Sport corrected for bet {bet_id}: {updated_count} legs updated to {new_sport}")
        
        return {
            'message': f'Sport corrected to {new_sport}',
            'legs_updated': updated_count,
            'sport': new_sport
        }, 200
    else:
        return {'message': 'No changes needed (sport already set to ' + new_sport + ')'}, 200


@bets_bp.route('/api/bets/<int:bet_id>/confidence', methods=['GET'])
@login_required
def get_sport_confidence(bet_id):
    """Task 10: Get sport detection confidence metrics for a bet.
    
    Returns detailed confidence scoring (0.0-1.0) for each leg's sport detection.
    Helps users identify low-confidence detections that may need correction.
    
    Response:
        {
            'bet_id': 123,
            'overall_confidence': 0.85,
            'legs': [
                {
                    'leg_index': 0,
                    'sport': 'NFL',
                    'confidence': 0.9,
                    'detection_method': 'team_name',
                    'games_found': true,
                    'recommendation': null
                },
                {
                    'leg_index': 1,
                    'sport': 'NBA',
                    'confidence': 0.3,
                    'detection_method': 'fallback',
                    'games_found': false,
                    'recommendation': 'Consider correcting sport - no games found on ESPN'
                }
            ]
        }
    """
    bet = Bet.query.get(bet_id)
    if not bet or not current_user.can_access(bet):
        return {'error': 'Bet not found'}, 404
    
    try:
        # Get bet data with confidence metadata
        bet_dict = bet.to_dict_structured(use_live_data=False)
        sport_metadata = bet_dict.get('sport_detection_metadata', {})
        confidence_data = sport_metadata.get('confidence_by_leg', [])
        
        # Calculate overall confidence as average of leg confidences
        if confidence_data:
            overall_confidence = sum(leg['confidence'] for leg in confidence_data) / len(confidence_data)
        else:
            overall_confidence = 0.5
        
        # Add recommendations based on confidence
        legs_with_recommendations = []
        for leg in confidence_data:
            recommendation = None
            confidence = leg.get('confidence', 0.5)
            
            # Low confidence (< 0.5) gets recommendation
            if confidence < 0.5:
                if not leg.get('games_found'):
                    recommendation = f"Consider correcting sport to '{leg.get('sport')}' - no games found on ESPN"
                else:
                    recommendation = f"Low confidence detection for {leg.get('sport')}. Please verify."
            elif confidence < 0.7 and not leg.get('games_found'):
                recommendation = "Medium confidence - verify if sport is correct"
            
            leg['recommendation'] = recommendation
            legs_with_recommendations.append(leg)
        
        return {
            'bet_id': bet_id,
            'overall_confidence': round(overall_confidence, 2),
            'confidence_rating': 'high' if overall_confidence >= 0.8 else 'medium' if overall_confidence >= 0.6 else 'low',
            'legs': legs_with_recommendations,
            'warnings': [
                f"Leg {leg['leg_index']}: {leg['recommendation']}"
                for leg in legs_with_recommendations
                if leg.get('recommendation')
            ]
        }, 200
    
    except Exception as e:
        logger.error(f"Error retrieving confidence data for bet {bet_id}: {e}")
        return {'error': 'Failed to retrieve confidence data'}, 500


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
		bets = get_user_bets_query(current_user, is_archived=True).options(db.joinedload(Bet.bet_legs_rel)).all()
		archived_parlays = [bet.to_dict_structured(use_live_data=True) for bet in bets]
		processed = process_parlay_data(archived_parlays)
		return jsonify({"archived": processed})
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
		return jsonify({
			'success': True,
			'user': current_user.to_dict()
		})
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
	# Removed synchronous automation calls - relying on background jobs
	# /live shows only bets with status='live'
	bets = get_user_bets_query(
		current_user,
		status='live',
		is_active=True,
		is_archived=False
	).options(db.joinedload(Bet.bet_legs_rel)).all()
	
	# Do NOT fetch live data synchronously
	live_parlays = [bet.to_dict_structured(use_live_data=False) for bet in bets]
	processed = process_parlay_data(live_parlays, fetch_live=False)
	return jsonify(sort_parlays_by_date(processed))

@bets_bp.route("/todays")
@login_required
@db_error_handler
def todays():
	# Removed synchronous automation calls - relying on background jobs
	
	# /todays shows only bets with status='pending'
	bets = get_user_bets_query(
		current_user,
		status='pending',
		is_active=True,
		is_archived=False
	).options(db.joinedload(Bet.bet_legs_rel)).all()
	
	todays_parlays = [bet.to_dict_structured(use_live_data=False) for bet in bets]
	processed = process_parlay_data(todays_parlays, fetch_live=False)
	return jsonify(sort_parlays_by_date(processed))

@bets_bp.route("/historical")
@login_required
@db_error_handler
def historical():
	from app import app  # Import here to avoid circular import
	from datetime import datetime, timedelta
	try:
		# Get pagination parameters
		page = request.args.get('page', 1, type=int)
		per_page = request.args.get('per_page', 50, type=int)
		
		# Get filter parameters
		filter_site = request.args.get('site', '').strip()
		filter_sport = request.args.get('sport', '').strip()
		filter_last_30_days = request.args.get('last_30_days', '').lower() == 'true'
		filter_search = request.args.get('search', '').strip().lower()
		
		# Clamp per_page to reasonable limits
		per_page = min(max(per_page, 10), 100)
		
		app.logger.info(f"[HISTORICAL] Request for user {current_user.id}: page={page}, per_page={per_page}, site={filter_site}, sport={filter_sport}, last_30_days={filter_last_30_days}, search={filter_search}")
		
		# Get base query for historical bets
		base_query = get_user_bets_query(
			current_user,
			status=['won', 'lost', 'completed']
		).options(db.joinedload(Bet.bet_legs_rel))
		
		# Apply filters BEFORE pagination
		
		# Filter by betting site (supports comma-separated multi-select)
		if filter_site:
			sites = [s.strip() for s in filter_site.split(',') if s.strip()]
			if len(sites) == 1:
				base_query = base_query.filter(Bet.betting_site == sites[0])
			elif len(sites) > 1:
				base_query = base_query.filter(Bet.betting_site.in_(sites))
		
		# Filter by sport (supports comma-separated multi-select, requires checking bet_legs)
		if filter_sport:
			sports = [s.strip() for s in filter_sport.split(',') if s.strip()]
			# Use exists() subquery for better performance
			from sqlalchemy import exists
			if len(sports) == 1:
				sport_subquery = db.session.query(BetLeg.bet_id).filter(
					BetLeg.bet_id == Bet.id,
					BetLeg.sport == sports[0]
				).exists()
			else:
				sport_subquery = db.session.query(BetLeg.bet_id).filter(
					BetLeg.bet_id == Bet.id,
					BetLeg.sport.in_(sports)
				).exists()
			base_query = base_query.filter(sport_subquery)
		
		# Filter by last 30 days
		if filter_last_30_days:
			cutoff_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
			base_query = base_query.filter(Bet.bet_date >= cutoff_date)
		
		# Filter by search term (searches in bet_data JSON, betting_site)
		if filter_search:
			search_pattern = f'%{filter_search}%'
			base_query = base_query.filter(
				or_(
					Bet.bet_data.ilike(search_pattern),
					Bet.betting_site.ilike(search_pattern)
				)
			)
		
		# Get total count for pagination metadata (AFTER filters applied)
		total_bets = base_query.count()
		total_pages = (total_bets + per_page - 1) // per_page  # Ceiling division
		
		# Handle edge case: requested page beyond available pages
		if page > total_pages and total_pages > 0:
			page = total_pages
		
		# Order by bet_date DESC for consistent pagination (newest first)
		bets = base_query.order_by(Bet.bet_date.desc(), Bet.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
		
		app.logger.info(f"[HISTORICAL] Found {len(bets)} bets for page {page} (total filtered: {total_bets})")
		
		historical_parlays = []
		for i, bet in enumerate(bets):
			try:
				bet_data = bet.to_dict_structured(use_live_data=False)
				historical_parlays.append(bet_data)
			except Exception as e:
				app.logger.error(f"[HISTORICAL] Error processing bet {bet.id}: {e}")
				continue
		
		app.logger.info(f"[HISTORICAL] Successfully processed {len(historical_parlays)} bets")
		
		# Process data for correct score_diff calculations
		processed_data = process_parlay_data(historical_parlays, fetch_live=False)
		
		# Sort within the page (should already be sorted by query, but ensures consistency)
		sorted_data = sort_parlays_by_date(processed_data)
		
		# Build active filters object for frontend
		active_filters = {}
		if filter_site:
			active_filters['site'] = filter_site
		if filter_sport:
			active_filters['sport'] = filter_sport
		if filter_last_30_days:
			active_filters['last_30_days'] = True
		if filter_search:
			active_filters['search'] = filter_search
		
		# Return paginated response with metadata
		return jsonify({
			'bets': sorted_data,
			'page': page,
			'per_page': per_page,
			'total_bets': total_bets,
			'total_pages': total_pages,
			'has_next': page < total_pages,
			'has_prev': page > 1,
			'filters': active_filters
		})
	except Exception as e:
		app.logger.error(f"[HISTORICAL] Unexpected error: {e}", exc_info=True)
		return jsonify({"error": str(e)}), 500

@bets_bp.route("/stats")
@login_required
@db_error_handler
def stats():
	auto_move_completed_bets(current_user.id)
	pending_bets = get_user_bets_query(current_user, status='pending').options(db.joinedload(Bet.bet_legs_rel)).all()
	parlays = [bet.to_dict_structured(use_live_data=True) for bet in pending_bets]
	processed_parlays = process_parlay_data(parlays)
	live_bets = get_user_bets_query(current_user, status='live').options(db.joinedload(Bet.bet_legs_rel)).all()
	live_parlays = [bet.to_dict_structured(use_live_data=True) for bet in live_bets]
	processed_live = process_parlay_data(live_parlays)
	return jsonify(sort_parlays_by_date(processed_live))

@bets_bp.route('/api/upload-betslip', methods=['POST'])
@login_required
@db_error_handler
def upload_betslip():
	"""Upload and process a bet slip image using OCR."""
	try:
		if 'image' not in request.files:
			return jsonify({'success': False, 'error': 'No image file provided'}), 400
		
		file = request.files['image']
		if file.filename == '':
			return jsonify({'success': False, 'error': 'No image file selected'}), 400
		
		if not file or not allowed_file(file.filename):
			return jsonify({'success': False, 'error': 'Invalid file type. Please upload a PNG, JPG, or JPEG image.'}), 400
		
		# Process the image with OCR
		try:
			extracted_data = process_betslip_image(file)
			return jsonify({
				'success': True,
				'data': extracted_data
			})
		except Exception as ocr_error:
			logger.error(f"OCR processing failed: {ocr_error}")
			return jsonify({
				'success': False,
				'error': f'Failed to process bet slip image: {str(ocr_error)}'
			}), 500
			
	except Exception as e:
		logger.error(f"Bet slip upload error: {e}")
		return jsonify({'success': False, 'error': str(e)}), 500

@bets_bp.route('/api/save-extracted-bet', methods=['POST'])
@login_required
def save_extracted_bet():
	"""Save an extracted/edited bet from bet slip processing."""
	try:
		data = request.get_json()
		if not data:
			return jsonify({'success': False, 'error': 'No data provided'}), 400
		
		# Transform the frontend data to match our internal format
		bet_data = transform_extracted_bet_data(data)
		
		# Validate required fields
		if not bet_data.get('legs'):
			return jsonify({'success': False, 'error': 'Bet must have at least one leg'}), 400
		
		# Save the bet
		from app import save_bet_to_db
		# Use the current logged-in user's ID
		# Skip duplicate check for OCR bets - they need their own BetLeg records created
		# Even if the wager/odds match another bet, OCR bets are separate instances
		result = save_bet_to_db(current_user.id, bet_data, skip_duplicate_check=True)
		
		return jsonify({
			'success': True,
			'bet': result,
			'message': 'Bet saved successfully'
		})
		
	except Exception as e:
		logger.error(f"Save extracted bet error: {e}", exc_info=True)
		# Ensure session is rolled back to recover from any transaction errors
		db.session.rollback()
		return jsonify({'success': False, 'error': str(e)}), 500

@bets_bp.route('/api/users', methods=['GET'])
@login_required
def get_users():
	"""Get list of all users for secondary bettor selection."""
	try:
		from models import User
		users = User.query.filter_by(is_active=True).all()
		user_list = [{
			'id': user.id,
			'username': user.username,
			'email': user.email
		} for user in users]
		
		return jsonify({'users': user_list})
		
	except Exception as e:
		logger.error(f"Get users error: {e}")
		return jsonify({'error': str(e)}), 500

def transform_extracted_bet_data(data):
	"""Transform frontend extracted bet data to internal format."""
	# datetime is now imported at module level
	
	# Map frontend field names to internal format
	# CRITICAL: bet_id (from OCR) → betting_site_id; bet_site (from OCR) → betting_site
	transformed = {
		'wager': float(data.get('wager_amount', 0)) if data.get('wager_amount') else None,
		'potential_winnings': float(data.get('potential_payout', 0)) if data.get('potential_payout') else None,
		'final_odds': data.get('total_odds'),
		'bet_date': data.get('bet_date'),
		'betting_site_id': data.get('bet_id'),  # Actual bet ID (e.g., "O/0240915/0000074" or "DK638926171300468480")
		'betting_site': data.get('bet_site'),  # Betting site name (DraftKings, FanDuel, etc.)
		'bet_type': data.get('bet_type', 'parlay'),
		'name': data.get('bet_name'),  # Save custom bet name
		'secondary_bettor_ids': data.get('secondary_bettor_ids', []),  # Include secondary bettors
		'legs': []
	}
	
	# Transform legs
	for leg in data.get('legs', []):
		# Determine the display bet type from the stat
		stat = leg.get('stat', '')
		display_bet_type = 'spread' if 'spread' in stat.lower() else \
		                  'moneyline' if 'moneyline' in stat.lower() or stat.lower() == 'ml' else \
		                  'total' if 'total' in stat.lower() or 'points' in stat.lower() else \
		                  stat.lower()
		
		# Determine home_team and away_team based on bet type
		team_name = leg.get('team', '')
		player_name = leg.get('player')
		
		if team_name == 'Game Total' or display_bet_type == 'total':
			# For totals, we don't have specific teams
			home_team = 'Game Total'
			away_team = 'Game Total'
			player_team = 'Game Total'
		elif display_bet_type == 'moneyline' or display_bet_type == 'spread':
			# For game bets, we need to identify both teams
			# For now, set the bet team as home and opponent as TBD - this will be resolved by ESPN API
			home_team = team_name
			away_team = 'TBD'  # Will be resolved by game matching
			player_team = team_name  # For game bets, player_team is the bet team
		else:
			# For player props, the team_name should be the player's team
			# If OCR extracted something wrong like "Total", we need better logic
			if player_name and team_name and team_name.lower() not in ['total', 'game total']:
				player_team = team_name
			else:
				# Try to extract team from player name context or use a default
				player_team = 'TBD'  # Will be resolved by player data population
			
			# For player props, we don't know the game teams yet
			home_team = player_team
			away_team = 'TBD'
		
		# Set default game_date for all OCR bets (they typically don't include dates)
		# Use Eastern timezone to ensure correct date regardless of server location
		eastern_tz = pytz.timezone('US/Eastern')
		default_game_date = dt_module.datetime.now(eastern_tz).strftime('%Y-%m-%d')
		
		# Better sport detection based on all major sports teams (FIX 2 & 3)
		nfl_teams = ['raiders', 'cowboys', 'chiefs', 'chargers', 'broncos', 'patriots', 'jets', 'giants', 'eagles', 'commanders', 'bears', 'lions', 'packers', 'vikings', 'falcons', 'panthers', 'saints', 'buccaneers', 'cardinals', 'rams', '49ers', 'seahawks', 'bengals', 'browns', 'steelers', 'ravens', 'bills', 'dolphins', 'texans', 'colts', 'jaguars', 'titans']
		nba_teams = ['lakers', 'celtics', 'warriors', 'bulls', 'heat', 'knicks', 'nets', 'sixers', 'raptors', 'bucks', 'suns', 'nuggets', 'clippers', 'mavericks', 'thunder', 'jazz', 'blazers', 'kings', 'wizards', 'hornets', 'pelicans', 'grizzlies', 'hawks', 'cavaliers', 'pistons', 'pacers', 'magic', 'spurs', 'rockets', 'timberwolves']
		mlb_teams = ['yankees', 'redsox', 'orioles', 'rays', 'bluejays', 'indians', 'guardians', 'twins', 'whitesox', 'royals', 'tigers', 'athletics', 'mariners', 'rangers', 'astros', 'angels', 'dodgers', 'padres', 'giants', 'rockies', 'braves', 'mets', 'nationals', 'marlins', 'phillies', 'cubs', 'cardinals', 'brewers', 'pirates', 'reds']
		nhl_teams = ['rangers', 'bruins', 'maple leafs', 'canadiens', 'devils', 'flyers', 'penguins', 'sabres', 'red wings', 'lightning', 'hurricanes', 'capitals', 'panthers', 'islanders', 'stars', 'avalanche', 'wild', 'blues', 'jets', 'blackhawks', 'canucks', 'flames', 'oilers', 'ducks', 'sharks', 'kings', 'desert']
		
		def detect_sport_from_stat_type(stat_type):
			"""Task 9: Infer sport from stat type using standardization mapping.
			
			Uses stat_standardization.py to map stat types to sports.
			Provides more comprehensive detection than hardcoded keywords.
			"""
			if not stat_type:
				return None
			
			stat_lower = stat_type.lower().strip()
			
			# Try each sport's stat map
			nfl_stats = get_all_stats_for_sport('NFL')
			nba_stats = get_all_stats_for_sport('NBA')
			mlb_stats = get_all_stats_for_sport('MLB')
			nhl_stats = get_all_stats_for_sport('NHL')
			
			# Standardize the stat type and check which sport it belongs to
			for sport, stat_list in [('NFL', nfl_stats), ('NBA', nba_stats), ('MLB', mlb_stats), ('NHL', nhl_stats)]:
				canonical = standardize_stat_type(stat_type, sport=sport)
				# If standardization returned a valid canonical stat (not the original), it matches
				if canonical in stat_list:
					return sport
			
			# Fallback to keyword matching for backwards compatibility
			if any(x in stat_lower for x in ['passing_yards', 'rushing_yards', 'sacks', 'interceptions', 'pass_completions', 'rushing_attempts', 'receiving_yards', 'receiving_touchdowns']):
				return 'NFL'
			elif any(x in stat_lower for x in ['three_pointers', 'rebounds', 'assists', 'steals', 'blocks', 'field_goals']):
				return 'NBA'
			elif any(x in stat_lower for x in ['home_runs', 'strikeouts', 'batting_average', 'rbi', 'hits', 'runs', 'stolen_bases']):
				return 'MLB'
			elif any(x in stat_lower for x in ['goals', 'shutouts', 'saves', 'penalty_minutes', 'shots_on_goal']):
				return 'NHL'
			
			return None
		
		team_lower = team_name.lower()
		sport = 'NFL'  # Default to NFL
		if any(nfl_team in team_lower for nfl_team in nfl_teams):
			sport = 'NFL'
		elif any(nba_team in team_lower for nba_team in nba_teams):
			sport = 'NBA'
		elif any(mlb_team in team_lower for mlb_team in mlb_teams):
			sport = 'MLB'
		elif any(nhl_team in team_lower for nhl_team in nhl_teams):
			sport = 'NHL'
		else:
			# Stat type fallback if team matching failed
			stat_type_sport = detect_sport_from_stat_type(leg.get('stat'))
			if stat_type_sport:
				logger.info(f"Detected sport '{stat_type_sport}' from stat type '{leg.get('stat')}' for team '{team_name}'")
				sport = stat_type_sport
		
		# Set target_value appropriately based on bet type
		if display_bet_type == 'moneyline':
			target_value = None  # Moneyline bets don't have a numeric target, they're win/loss only
		else:
			target_value = leg.get('line')
		
		# Standardize the stat type to canonical name
		raw_stat_type = leg.get('stat')
		standardized_stat = standardize_stat_type(raw_stat_type, sport=sport)
		
		transformed_leg = {
			'player_name': player_name,
			'team_name': team_name,
			'stat_type': standardized_stat,  # Use standardized stat type
			'bet_type': 'Team Prop' if display_bet_type in ['moneyline', 'spread', 'total', 'total_points'] else 'Player Prop',
			'target_value': target_value,
			'bet_line_type': 'over' if leg.get('stat_add') == 'over' else 'under' if leg.get('stat_add') == 'under' else None,
			'odds': leg.get('odds'),
			# Required BetLeg fields - provide proper defaults for OCR bets
			'home_team': home_team,
			'away_team': away_team,
			'player_team': player_team,  # Add player_team for proper assignment
			'sport': sport,
			'game_date': default_game_date,  # Default to today for OCR bets
			'status': 'pending'  # Set default status for OCR bets
		}
		
		# FIX: Ensure Anytime Touchdown bets have a target of 1.0 (implied "at least 1")
		# If target is 0 or None, the hit logic (achieved >= target) would mark 0 TDs as a win!
		if transformed_leg['stat_type'] == 'anytime_touchdown':
			if not transformed_leg['target_value'] or float(transformed_leg['target_value']) == 0:
				transformed_leg['target_value'] = 1.0
				
		transformed['legs'].append(transformed_leg)
	
	return transformed

@bets_bp.route('/issues')
@login_required
def issues():
	"""Issues tracking page - only visible to user 'manishslal' (user.id = 1)"""
	if current_user.id != 1:
		return jsonify({"error": "Access denied"}), 403
	
	# For now, return a simple list of issues. This will be expanded later.
	issues_list = [
		"1. Historical bets API fetching automation - Not implemented yet",
		"2. Player linking for bet_legs - Not implemented yet", 
		"3. ESPN data population for historical games - Not implemented yet",
		"4. Auto-move old bets to historical - Not implemented yet"
	]
	
	return jsonify({
		"issues": issues_list,
		"total_issues": len(issues_list)
	})

@bets_bp.route("/api/cache-bust", methods=['POST'])
@login_required
@db_error_handler
def cache_bust():
	"""Clear the game data cache to force fresh ESPN data on next request."""
	from services.bet_service import clear_game_cache
	
	try:
		clear_game_cache()  # Clear all cached game data
		
		# TRIGGER AUTOMATION: 
		# 1. Update live bet legs (fetch fresh data from ESPN and save to DB)
		# 2. Run hit status determination (check if new data means a win/loss)
		# This ensures that when user clicks "Refresh Stats", we update the database status
		# to match the latest data, including early wins/losses.
		try:
			from automation.live_bet_updates import update_live_bet_legs
			from automation.bet_status_management import auto_determine_leg_hit_status
			
			logger.info("Triggering update_live_bet_legs from cache-bust")
			update_live_bet_legs()
			
			logger.info("Triggering auto_determine_leg_hit_status from cache-bust")
			auto_determine_leg_hit_status()
		except Exception as e:
			logger.error(f"Error running automation from cache-bust: {e}")
			
		return jsonify({
			'success': True,
			'message': 'Game cache cleared, data updated, and status checked.'
		})
	except Exception as e:
		logger.error(f"Error clearing cache: {e}")
		return jsonify({
			'success': False,
			'error': str(e)
		}), 500

