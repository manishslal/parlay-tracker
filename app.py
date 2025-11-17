from services import compute_and_persist_returns
# Define run_migrations_once before usage
from flask import Flask, jsonify, send_from_directory, request, session
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import requests
import os
import time
from datetime import datetime
import json
import atexit
from flask import Flask, jsonify, send_from_directory, request, session
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import requests
import os
import time
from datetime import datetime
import json
import atexit

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Import database models
from models import db, User, Bet, BetLeg, Player
from helpers.database import run_migrations_once, has_complete_final_data, save_final_results_to_bet, auto_move_completed_bets


from helpers.utils import data_path, DATA_DIR

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Flask app initialization and config
app = Flask(__name__, static_folder='.', static_url_path='')

# Register blueprints
 # Serve index.html at root
@app.route('/')
def index():
    return app.send_static_file('index.html')

# Explicitly serve service worker for PWA functionality
@app.route('/service-worker.js')
def service_worker():
    return app.send_static_file('service-worker.js')

# Serve manifest.json for PWA
@app.route('/manifest.json')
def manifest():
    return app.send_static_file('manifest.json')

from routes.admin import admin_bp
from routes.auth import auth_bp
from routes import bets_bp
app.register_blueprint(admin_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(bets_bp)  # No url_prefix, endpoints at root

# Database configuration

database_url = os.environ.get('DATABASE_URL')
if not database_url:
    raise RuntimeError("DATABASE_URL environment variable must be set for PostgreSQL connection.")
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
if database_url.startswith('postgresql://'):
    if '?' in database_url:
        database_url += '&sslmode=require'
    else:
        database_url += '?sslmode=require'
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,  # Maximum number of connections in the pool
    'max_overflow': 20,  # Maximum number of connections that can be created beyond pool_size
    'pool_timeout': 30,  # Timeout for getting a connection from the pool
    'pool_recycle': 3600,  # Recycle connections after 1 hour (helps with stale connections)
    'pool_pre_ping': True,  # Enable connection health checks
    'connect_args': {
        'connect_timeout': 10,  # Connection timeout in seconds
        'options': '-c statement_timeout=30000'  # Query timeout (30 seconds)
    }
}
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 2592000
app.config['SESSION_COOKIE_SECURE'] = False
app.config['REMEMBER_COOKIE_DURATION'] = 2592000
CORS(app, supports_credentials=True)
db.init_app(app)

from functools import wraps
from helpers.utils import (
    compute_parlay_returns_from_odds,
    sort_parlays_by_date,
    get_events,
    calculate_bet_value,
    _get_player_stat_from_boxscore,
    _get_touchdowns
)

from typing import Any
def get_user_bets_query(user: Any, **filters: Any) -> Any:
    """
    Get bets for a user using array containment.
    This returns all bets the user has access to (owned + shared + watched).
    
    Args:
        user: User object
        **filters: Additional filters (status, is_active, is_archived, etc.)
    
    Returns:
        SQLAlchemy query object
    """
    from sqlalchemy import or_
    
    # Query bets where user is primary, secondary bettor, or watcher
    query = Bet.query.filter(
        or_(
            Bet.user_id == user.id,  # Primary bettor
            Bet.secondary_bettors.contains([user.id]),  # Secondary bettor
            Bet.watchers.contains([user.id])  # Watcher
        )
    )
    
    # Apply additional filters
    for key, value in filters.items():
        if hasattr(Bet, key):
            if isinstance(value, list):
                query = query.filter(getattr(Bet, key).in_(value))
            else:
                query = query.filter(getattr(Bet, key) == value)
    return query


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


def retry_db_operation(operation, max_retries=2, delay=1):
    """Retry a database operation with exponential backoff."""
    import time
    
    for attempt in range(max_retries + 1):
        try:
            return operation()
        except Exception as e:
            error_msg = str(e).lower()
            if 'timeout' in error_msg or 'connection' in error_msg or 'ssl' in error_msg:
                if attempt < max_retries:
                    wait_time = delay * (2 ** attempt)  # Exponential backoff
                    time.sleep(wait_time)
                    continue
                else:
                    raise
            else:
                # Don't retry non-connection errors
                raise
    
    return None


# Directly run migrations after app and blueprints are set up
run_migrations_once(app)

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    """Decorator to require admin role for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        if not current_user.is_admin():
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

## Migration logic moved to helpers/database.py

# Setup background scheduler for automated tasks
scheduler = BackgroundScheduler()
scheduler.start()

# Shut down scheduler on app exit
atexit.register(lambda: scheduler.shutdown())

# Helper function to use database with JSON backup
from typing import Optional, List
def get_user_bets_from_db(user_id: int, status_filter: Optional[Any] = None) -> List[Any]:
    """Get bets from database for a specific user, returns Bet objects"""
    try:
        query = Bet.query.filter_by(user_id=user_id)
        if status_filter:
            if isinstance(status_filter, list):
                query = query.filter(Bet.status.in_(status_filter))
            else:
                query = query.filter_by(status=status_filter)
        bets = query.order_by(Bet.created_at.desc()).all()
        return bets  # Return Bet objects, not dicts
    except Exception as e:
        app.logger.error(f"Database error: {e}, falling back to JSON")
        return []

def populate_game_ids_for_bet(bet: Any) -> None:
    """Populate ESPN game IDs for all bet legs in a bet that have game dates and team info."""
    from helpers.espn_api import get_espn_games_with_ids_for_date
    from datetime import datetime, timedelta
    
    bet_legs = db.session.query(BetLeg).filter(
        BetLeg.bet_id == bet.id,
        BetLeg.game_date.isnot(None),
        BetLeg.away_team.isnot(None),
        BetLeg.home_team.isnot(None),
        (BetLeg.game_id.is_(None) | (BetLeg.game_id == ''))
    ).all()
    
    if not bet_legs:
        return  # No legs need game ID population
    
    app.logger.info(f"[GAME-ID-POPULATION] Populating game IDs for {len(bet_legs)} legs in bet {bet.id}")
    
    # Group legs by game date for efficiency
    legs_by_date = {}
    for leg in bet_legs:
        date_key = leg.game_date
        if date_key not in legs_by_date:
            legs_by_date[date_key] = []
        legs_by_date[date_key].append(leg)
    
    # Process each date
    for game_date, legs in legs_by_date.items():
        try:
            # Get games with IDs for this date
            games = get_espn_games_with_ids_for_date(game_date)
            if not games:
                app.logger.warning(f"[GAME-ID-POPULATION] No games found for date {game_date}")
                continue
            
            # Create lookup map for faster matching
            game_lookup = {}
            for game_id, espn_away, espn_home in games:
                # Normalize team names for matching
                away_norm = espn_away.lower().strip()
                home_norm = espn_home.lower().strip()
                key = f"{away_norm}@{home_norm}"
                game_lookup[key] = game_id
                
                # Also try reverse order
                reverse_key = f"{home_norm}@{away_norm}"
                game_lookup[reverse_key] = game_id
            
            # Match each leg to a game
            for leg in legs:
                away_norm = leg.away_team.lower().strip()
                home_norm = leg.home_team.lower().strip()
                key = f"{away_norm}@{home_norm}"
                
                if key in game_lookup:
                    leg.game_id = game_lookup[key]
                    app.logger.info(f"[GAME-ID-POPULATION] Set game_id {game_lookup[key]} for leg {leg.id} ({leg.away_team} @ {leg.home_team})")
                else:
                    app.logger.warning(f"[GAME-ID-POPULATION] No game match found for leg {leg.id}: {leg.away_team} @ {leg.home_team} on {game_date}")
        
        except Exception as e:
            app.logger.error(f"[GAME-ID-POPULATION] Error processing date {game_date}: {e}")
    
    # Commit all changes
    try:
        db.session.commit()
        app.logger.info(f"[GAME-ID-POPULATION] Successfully populated game IDs for bet {bet.id}")
    except Exception as e:
        app.logger.error(f"[GAME-ID-POPULATION] Error committing changes for bet {bet.id}: {e}")
        db.session.rollback()

def populate_player_data_for_bet(bet: Any) -> None:
    """Populate player_id and player_position for all bet legs in a bet."""
    from helpers.espn_api import search_espn_player
    from models import Player
    
    bet_legs = db.session.query(BetLeg).filter(
        BetLeg.bet_id == bet.id,
        BetLeg.player_name.isnot(None),
        BetLeg.player_name != 'Unknown',
        BetLeg.player_id.is_(None)
    ).all()
    
    if not bet_legs:
        return  # No legs need player data population
    
    app.logger.info(f"[PLAYER-POPULATION] Populating player data for {len(bet_legs)} legs in bet {bet.id}")
    
    for leg in bet_legs:
        try:
            # First, try to find existing player by name
            existing_player = Player.query.filter(
                db.or_(
                    Player.player_name == leg.player_name,
                    Player.normalized_name == leg.player_name.lower().strip(),
                    Player.display_name == leg.player_name
                )
            ).first()
            
            if existing_player:
                # Use existing player
                leg.player_id = existing_player.id
                leg.player_position = existing_player.position
                app.logger.info(f"[PLAYER-POPULATION] Found existing player {existing_player.player_name} (ID: {existing_player.id}) for leg {leg.id}")
                continue
            
            # Player not found, search ESPN
            app.logger.info(f"[PLAYER-POPULATION] Player {leg.player_name} not found locally, searching ESPN...")
            espn_player_data = search_espn_player(leg.player_name, sport="football", league="nfl")
            
            if espn_player_data:
                # Create new player record
                new_player = Player(
                    player_name=espn_player_data['player_name'],
                    normalized_name=espn_player_data['player_name'].lower().strip(),
                    display_name=espn_player_data['player_name'],
                    sport=espn_player_data['sport'],
                    position=espn_player_data['position'],
                    jersey_number=espn_player_data['jersey_number'],
                    current_team=espn_player_data['current_team'],
                    team_abbreviation=espn_player_data['team_abbreviation'],
                    espn_player_id=espn_player_data['espn_player_id']
                )
                
                db.session.add(new_player)
                db.session.flush()  # Get the ID
                
                # Update the bet leg
                leg.player_id = new_player.id
                leg.player_position = new_player.position
                
                app.logger.info(f"[PLAYER-POPULATION] Created new player {new_player.player_name} (ID: {new_player.id}, ESPN ID: {new_player.espn_player_id}) for leg {leg.id}")
            else:
                app.logger.warning(f"[PLAYER-POPULATION] Player {leg.player_name} not found on ESPN for leg {leg.id}")
        
        except Exception as e:
            app.logger.error(f"[PLAYER-POPULATION] Error processing player {leg.player_name} for leg {leg.id}: {e}")
    
    # Commit all changes
    try:
        db.session.commit()
        app.logger.info(f"[PLAYER-POPULATION] Successfully populated player data for bet {bet.id}")
    except Exception as e:
        app.logger.error(f"[PLAYER-POPULATION] Error committing changes for bet {bet.id}: {e}")
        db.session.rollback()

def save_bet_to_db(user_id: int, bet_data: dict) -> dict:
    """Save a bet to database with JSON backup and create BetLeg records"""
    from models import Team, Bet, BetLeg

    # --- DUPLICATE CHECK LOGIC ---
    legs = bet_data.get('legs', [])
    core_fields = ['wager', 'payout', 'odds', 'placed_at']
    core_match = {f: bet_data.get(f) for f in core_fields}

    # Query all bets for user
    user_bets = Bet.query.filter_by(user_id=user_id).all()
    for existing_bet in user_bets:
        existing_data = existing_bet.get_bet_data()
        # ...existing code for duplicate detection...
            # Check for duplicate bets
        if existing_data['wager'] == core_match['wager'] and existing_data['odds'] == core_match['odds']:
                app.logger.info(f"[DUPLICATE CHECK] Bet already exists for user {user_id}.")
                return existing_bet.to_dict()

    # --- NORMALIZATION AND SAVE LOGIC ---
    teams = Team.query.all()
    team_lookup = {}
    for sport in ['NFL', 'NBA']:
            sport_teams = [t for t in teams if t.sport == sport]
            abbr_to_nickname = {}
            name_to_nickname = {}
            for team in sport_teams:
                if team.nickname:
                    if team.team_abbr:
                        abbr_to_nickname[team.team_abbr.upper().strip()] = team.nickname
                    if team.team_name:
                        name_to_nickname[team.team_name.lower().strip()] = team.nickname
                    if team.team_name_short:
                        name_to_nickname[team.team_name_short.lower().strip()] = team.nickname
            team_lookup[sport] = {
                'abbr_to_nickname': abbr_to_nickname,
                'name_to_nickname': name_to_nickname
            }

    def normalize_team_name(team_str, sport):
        if not team_str or not sport or sport not in team_lookup:
            return team_str
        lookup = team_lookup[sport]
        team_lower = team_str.lower().strip()
        team_upper = team_str.upper().strip()
        if team_upper in lookup['abbr_to_nickname']:
            return lookup['abbr_to_nickname'][team_upper]
        if team_lower in lookup['name_to_nickname']:
            return lookup['name_to_nickname'][team_lower]
        for full_name, nickname in lookup['name_to_nickname'].items():
            if full_name in team_lower or team_lower in full_name:
                return nickname
        return team_str

    bet = Bet(user_id=user_id)
    import json
    bet.bet_data = json.dumps(bet_data)
    bet.is_active = True
    bet.is_archived = False
    bet.status = 'pending'
    bet.api_fetched = 'No'
    db.session.add(bet)
    db.session.flush()

    for leg_data in legs:
            game_date = None
            game_time = None
            if leg_data.get('game_date'):
                try:
                    from datetime import datetime as dt
                    game_datetime = dt.fromisoformat(leg_data['game_date'].replace('Z', '+00:00'))
                    game_date = game_datetime.date()
                    game_time = game_datetime.time()
                except (ValueError, AttributeError):
                    pass
            sport = leg_data.get('sport', 'NFL')
            team_value = leg_data.get('team')
            if team_value:
                team_value = normalize_team_name(team_value, sport)
            leg_status = leg_data.get('status', 'pending')
            bet_leg = BetLeg(
                bet_id=bet.id,
                player_name=leg_data.get('player') or team_value or 'Unknown',
                player_team=team_value,
                home_team=leg_data.get('home_team', ''),
                away_team=leg_data.get('away_team', ''),
                game_date=game_date,
                game_time=game_time,
                sport=sport,
                bet_type=leg_data.get('bet_type', 'player_prop'),
                bet_line_type=leg_data.get('bet_line_type'),
                target_value=leg_data.get('line') or 0.0,
                stat_type=leg_data.get('stat'),
                status=leg_status,
                leg_order=leg_data.get('leg_order', 0)
            )
            if leg_status == 'won':
                bet_leg.is_hit = True
            elif leg_status == 'lost':
                bet_leg.is_hit = False
            if leg_data.get('odds'):
                try:
                    odds_str = str(leg_data['odds']).strip()
                    if odds_str.startswith('+') or odds_str.startswith('-'):
                        bet_leg.final_leg_odds = int(odds_str.replace('+', ''))
                    else:
                        bet_leg.final_leg_odds = int(odds_str)
                except (ValueError, AttributeError):
                    pass
            db.session.add(bet_leg)
    db.session.commit()
    backup_to_json(user_id)
    
    # Populate ESPN game IDs for the newly created bet legs
    try:
        populate_game_ids_for_bet(bet)
    except Exception as e:
        app.logger.error(f"[GAME-ID-POPULATION] Error populating game IDs for bet {bet.id}: {e}")
    
    # Populate player data for the newly created bet legs
    try:
        populate_player_data_for_bet(bet)
    except Exception as e:
        app.logger.error(f"[PLAYER-POPULATION] Error populating player data for bet {bet.id}: {e}")
    
    # ESPN API update trigger
    try:
        update_bet_legs_for_bet(bet)
    except Exception as e:
        app.logger.error(f"[ESPN-UPDATE] Error updating bet legs for bet {bet.id}: {e}")
    return bet.to_dict()
    # --- ESPN API single bet update ---
def update_bet_legs_for_bet(bet: Any) -> None:
    """Update bet legs for a single bet using ESPN API logic."""
    bet_legs = db.session.query(BetLeg).filter(BetLeg.bet_id == bet.id).order_by(BetLeg.leg_order).all()
    needs_update = False
    for leg in bet_legs:
        # Only update if game is not final or stats missing
        if leg.game_status != 'STATUS_FINAL' or leg.achieved_value is None or leg.status == 'pending':
            needs_update = True
            break
    if not needs_update:
        return
    try:
        bet_data = bet.to_dict_structured(use_live_data=True)
        processed_data = process_parlay_data([bet_data])
        if not processed_data:
            return
        matching_parlay = processed_data[0]
        for i, bet_leg in enumerate(bet_legs):
            if i >= len(matching_parlay.get('legs', [])):
                continue
            processed_leg = matching_parlay['legs'][i]
            # Only process if game is final or stats available
            if processed_leg.get('gameStatus') != 'STATUS_FINAL' and processed_leg.get('current') is None:
                continue
            # Update achieved_value from current stats
            if processed_leg.get('current') is not None and bet_leg.achieved_value is None:
                bet_leg.achieved_value = processed_leg['current']
            # Update game status
            if processed_leg.get('gameStatus') == 'STATUS_FINAL' and bet_leg.game_status != 'STATUS_FINAL':
                bet_leg.game_status = 'STATUS_FINAL'
            # Update final scores
            if processed_leg.get('homeScore') is not None:
                bet_leg.home_score = processed_leg['homeScore']
                bet_leg.away_score = processed_leg['awayScore']
            # Calculate and save leg status (won/lost)
            if bet_leg.status == 'pending' and bet_leg.is_hit is None and bet_leg.achieved_value is not None:
                leg_status = 'lost'
                stat_type = bet_leg.bet_type.lower()
                if stat_type == 'moneyline':
                    leg_status = 'won' if bet_leg.achieved_value > 0 else 'lost'
                elif stat_type == 'spread':
                    if bet_leg.target_value is not None:
                        leg_status = 'won' if (bet_leg.achieved_value + bet_leg.target_value) > 0 else 'lost'
                else:
                    if bet_leg.target_value is not None:
                        if bet_leg.bet_line_type == 'under':
                            leg_status = 'won' if bet_leg.achieved_value < bet_leg.target_value else 'lost'
                        else:
                            leg_status = 'won' if bet_leg.achieved_value >= bet_leg.target_value else 'lost'
                bet_leg.status = leg_status
                bet_leg.is_hit = True if leg_status == 'won' else False
        db.session.commit()
    except Exception as e:
        app.logger.error(f"[ESPN-UPDATE] Error in update_bet_legs_for_bet: {e}")
        db.session.rollback()
    except Exception as e:
        app.logger.error(f"Error saving bet to database: {e}")
        db.session.rollback()
        raise

def has_complete_final_data(bet_data: dict) -> bool:
    """Check if a bet has complete final data for all legs
    
    Returns True if all legs have final_value OR current stats saved (not None).
    This indicates the bet doesn't need ESPN API fetching anymore.
    """
    legs = bet_data.get('legs', [])
    if not legs:
        return False
    
    for leg in legs:
        # Check if leg has final data stored (not just the key, but actual data)
        has_final = leg.get('final_value') is not None or leg.get('current') is not None
        if not has_final:
            return False
    
    return True


from typing import List
def save_final_results_to_bet(bet: Any, processed_data: List[dict]) -> bool:
    """Save final game results to bet data when games are completed
    
    This preserves final scores and outcomes so we don't lose data when ESPN
    removes old games from their API. Saves to both JSON bet_data and BetLeg table.
    """
    try:
        bet_data = bet.get_bet_data()
        
        # Find the matching processed parlay data
        matching_parlay = None
        for p in processed_data:
            if p.get('bet_id') == bet_data.get('bet_id') or p.get('name') == bet_data.get('name'):
                matching_parlay = p
                break
        
        if not matching_parlay:
            return False
        
        # Get BetLeg objects for this bet
        bet_legs = db.session.query(BetLeg).filter(BetLeg.bet_id == bet.id).order_by(BetLeg.leg_order).all()
        
        # Update each leg with final results
        updated = False
        for i, leg in enumerate(bet_data.get('legs', [])):
            # Find matching leg in processed data
            if i < len(matching_parlay.get('legs', [])):
                processed_leg = matching_parlay['legs'][i]
                
                # Save final stats if game is complete
                if processed_leg.get('gameStatus') == 'STATUS_FINAL':
                    # Store final score
                    if 'score' not in leg:
                        leg['score'] = processed_leg.get('score', {})
                        updated = True
                    
                    # Store final player/team stats
                    if 'final_value' not in leg and 'current' in processed_leg:
                        leg['final_value'] = processed_leg['current']
                        updated = True
                    
                    # Store game result (won/lost)
                    if 'result' not in leg and 'status' in processed_leg:
                        leg['result'] = processed_leg['status']
                        updated = True
                    
                    # Also save to BetLeg table for future queries
                    if i < len(bet_legs):
                        bet_leg = bet_legs[i]
                        if processed_leg.get('current') is not None and bet_leg.achieved_value is None:
                            bet_leg.achieved_value = processed_leg['current']
                            updated = True
                            app.logger.info(f"Saved achieved_value={processed_leg['current']} for leg {i}: {bet_leg.player_name or bet_leg.team}")
                        
                        # Save game status
                        if bet_leg.game_status != 'STATUS_FINAL':
                            bet_leg.game_status = 'STATUS_FINAL'
                            updated = True
                        
                        # Save final scores
                        if processed_leg.get('homeScore') is not None:
                            bet_leg.home_score = processed_leg['homeScore']
                            bet_leg.away_score = processed_leg['awayScore']
                            updated = True
                        
                        # Calculate and save leg status (won/lost) based on bet type
                        if bet_leg.status == 'pending':
                            leg_status = 'lost'  # Default to lost
                            stat_type = bet_leg.bet_type.lower()
                            
                            if stat_type == 'moneyline':
                                # Moneyline: won if score_diff > 0
                                leg_status = 'won' if bet_leg.achieved_value and bet_leg.achieved_value > 0 else 'lost'
                            elif stat_type == 'spread':
                                # Spread: won if (score_diff + spread) > 0
                                if bet_leg.achieved_value is not None and bet_leg.target_value is not None:
                                    leg_status = 'won' if (bet_leg.achieved_value + bet_leg.target_value) > 0 else 'lost'
                            else:
                                # Player props: won if achieved_value >= target_value
                                if bet_leg.achieved_value is not None and bet_leg.target_value is not None:
                                    # Check for over/under
                                    if bet_leg.bet_line_type == 'under':
                                        leg_status = 'won' if bet_leg.achieved_value < bet_leg.target_value else 'lost'
                                    else:  # 'over' or None (default to over)
                                        leg_status = 'won' if bet_leg.achieved_value >= bet_leg.target_value else 'lost'
                            
                            bet_leg.status = leg_status
                            bet_leg.is_hit = True if leg_status == 'won' else False
                            updated = True
                            app.logger.info(f"Set status={leg_status}, is_hit={bet_leg.is_hit} for leg {i}: {bet_leg.player_name or bet_leg.team}")
        
        # Save back to database if updated
        if updated:
            bet.set_bet_data(bet_data, preserve_status=True)
            db.session.commit()
            app.logger.info(f"Saved final results for bet {bet.id}")
            return True
            
    except Exception as e:
        app.logger.error(f"Error saving final results: {e}")
        db.session.rollback()
    
    return False

def auto_move_completed_bets(user_id):
    """Automatically move bets to historical when:
    1. Any leg is a confirmed loss (Miss) - bet is dead, but keep fetching until all games finish
    2. All games have finished (STATUS_FINAL) - bet outcome is final
    
    This moves bets immediately rather than waiting until the next day.
    Also saves final game results before moving to completed status.
    """
    try:
        from datetime import date
        today = date.today()
        
        # Get all pending and live bets for user
        bets = get_user_bets_from_db(user_id, status_filter=['pending', 'live'])
        
        # First, process all bets to get current data from ESPN
        # Use to_dict_structured() to get legs from database, not JSON blob
        bet_data_list = [bet.to_dict_structured(use_live_data=True) for bet in bets]
        processed_data = process_parlay_data(bet_data_list)
        
        updated_count = 0
        for bet in bets:
            bet_data = bet.to_dict_structured(use_live_data=True)
            legs = bet_data.get('legs', [])
            
            if not legs:
                continue
            
            # Find matching processed data for this bet
            matching_processed = None
            for p in processed_data:
                if p.get('bet_id') == bet_data.get('bet_id') or p.get('name') == bet_data.get('name'):
                    matching_processed = p
                    break
            
            if not matching_processed:
                continue
            
            # Check two conditions for moving to historical:
            # 1. Does any leg have a confirmed loss (Miss)?
            # 2. Are all games finished (STATUS_FINAL)?
            
            has_confirmed_loss = False
            all_games_finished = True
            games_data = matching_processed.get('games', [])
            
            for i, leg in enumerate(legs):
                # Find corresponding processed leg
                processed_leg = matching_processed.get('legs', [])[i] if i < len(matching_processed.get('legs', [])) else None
                
                if not processed_leg:
                    continue
                
                # Find game data for this leg
                # Match by either full name or abbreviation (database stores abbreviations, API returns both)
                game_data = None
                leg_away = leg.get('away', '')
                leg_home = leg.get('home', '')
                
                for game in games_data:
                    teams = game.get('teams', {})
                    game_away = teams.get('away', '')
                    game_home = teams.get('home', '')
                    game_away_abbr = teams.get('away_abbr', '')
                    game_home_abbr = teams.get('home_abbr', '')
                    
                    # Check if teams match (compare abbreviations or full names)
                    away_match = (leg_away == game_away or 
                                  leg_away == game_away_abbr or
                                  game_away == leg_away or
                                  game_away_abbr == leg_away)
                    home_match = (leg_home == game_home or 
                                  leg_home == game_home_abbr or
                                  game_home == leg_home or
                                  game_home_abbr == leg_home)
                    
                    if away_match and home_match:
                        game_data = game
                        break
                
                if not game_data:
                    # No game data means game not finished yet
                    all_games_finished = False
                    continue
                
                game_status = game_data.get('statusTypeName', '')
                
                # Check if game is finished
                if game_status != 'STATUS_FINAL':
                    all_games_finished = False
                else:
                    # Game is final - check if this leg is a loss
                    is_spread_or_ml = leg.get('stat') in ['spread', 'moneyline']
                    current = processed_leg.get('current', 0)
                    target = leg.get('target', 0)
                    
                    if is_spread_or_ml:
                        # For spread/moneyline, check if bet lost
                        score_diff = leg.get('score_diff', processed_leg.get('score_diff', 0))
                        
                        if leg.get('stat') == 'moneyline':
                            # Moneyline: team must win (score_diff > 0)
                            if score_diff <= 0:
                                has_confirmed_loss = True
                                app.logger.info(f"Bet {bet.id} - Leg {i+1} MISS (moneyline lost)")
                        elif leg.get('stat') == 'spread':
                            # Spread: (score_diff + spread) must be > 0
                            if (score_diff + target) <= 0:
                                has_confirmed_loss = True
                                app.logger.info(f"Bet {bet.id} - Leg {i+1} MISS (spread not covered)")
                    else:
                        # For regular player props/totals
                        # Check if final and missed target
                        if target > 0:
                            pct = (current / target) * 100
                            
                            # Check for over/under bets
                            stat_add = leg.get('stat_add') or leg.get('over_under')
                            
                            if leg.get('stat') in ['total_points', 'total_points_under', 'total_points_over']:
                                # Total points bet
                                is_under = stat_add == 'under' or leg.get('stat') == 'total_points_under'
                                is_over = stat_add == 'over' or leg.get('stat') == 'total_points_over'
                                
                                if is_under and current >= target:
                                    has_confirmed_loss = True
                                    app.logger.info(f"Bet {bet.id} - Leg {i+1} MISS (total under failed)")
                                elif is_over and current <= target:
                                    has_confirmed_loss = True
                                    app.logger.info(f"Bet {bet.id} - Leg {i+1} MISS (total over failed)")
                            elif stat_add == 'under':
                                # Player stat under
                                if current >= target:
                                    has_confirmed_loss = True
                                    app.logger.info(f"Bet {bet.id} - Leg {i+1} MISS (under failed)")
                            else:
                                # Regular over bet or no stat_add (assume over)
                                if current < target:
                                    has_confirmed_loss = True
                                    app.logger.info(f"Bet {bet.id} - Leg {i+1} MISS (target not reached)")
            
            # Decide whether to move to historical
            should_move = False
            move_reason = ""
            
            if has_confirmed_loss:
                should_move = True
                move_reason = "has confirmed loss"
                # Don't mark as fully complete yet if games are still in progress
                # This allows continued ESPN fetching until all games finish
                if not all_games_finished:
                    bet.status = 'live'  # Keep as live to continue fetching
                    bet.api_fetched = 'No'  # Keep fetching until all games done
                else:
                    bet.status = 'completed'
                    bet.api_fetched = 'Yes'
                    save_final_results_to_bet(bet, processed_data)
            elif all_games_finished:
                should_move = True
                move_reason = "all games finished"
                bet.status = 'completed'
                bet.api_fetched = 'Yes'
                save_final_results_to_bet(bet, processed_data)
            
            if should_move:
                app.logger.info(f"Auto-moving bet {bet.id} to historical ({move_reason})")
                bet.is_active = False  # Move to historical
                updated_count += 1
        
        # Commit all changes at once
        if updated_count > 0:
            db.session.commit()
            app.logger.info(f"Auto-moved {updated_count} bets to historical")
            
    except Exception as e:
        app.logger.error(f"Error auto-moving completed bets: {e}")
        db.session.rollback()

def update_completed_bet_legs():
    """Background job to automatically update bet legs when games become final.
    
    Finds all bets with status='completed' and checks their legs:
    - If a leg's game_status changes to STATUS_FINAL for the first time
    - Fetches final stats from ESPN
    - Updates achieved_value, status (won/lost), and final scores in bet_legs table
    
    This runs periodically (every 30 minutes) to ensure completed bets get their final results.
    """
    try:
        app.logger.info("[AUTO-UPDATE] Starting bet leg update check...")
        
        # Get all completed bets that might have pending leg updates
        completed_bets = Bet.query.filter_by(status='completed').all()
        
        if not completed_bets:
            app.logger.info("[AUTO-UPDATE] No completed bets found")
            return
        
        app.logger.info(f"[AUTO-UPDATE] Checking {len(completed_bets)} completed bets")
        
        updated_bets = 0
        updated_legs = 0
        
        for bet in completed_bets:
            # Get bet legs from database
            bet_legs = db.session.query(BetLeg).filter(BetLeg.bet_id == bet.id).order_by(BetLeg.leg_order).all()
            
            # Check if any legs need updating (have STATUS_FINAL but no achieved_value or pending status)
            needs_update = False
            for leg in bet_legs:
                if leg.game_status == 'STATUS_FINAL' and (leg.achieved_value is None or leg.status == 'pending'):
                    needs_update = True
                    break
            
            if not needs_update:
                continue
            
            try:
                # Get fresh data from ESPN for this bet
                bet_data = bet.to_dict_structured(use_live_data=True)
                processed_data = process_parlay_data([bet_data])
                
                if not processed_data:
                    continue
                
                matching_parlay = processed_data[0]
                
                # Update each leg with final results
                for i, bet_leg in enumerate(bet_legs):
                    # Skip if already processed
                    if bet_leg.achieved_value is not None and bet_leg.status != 'pending':
                        continue
                    
                    # Get processed leg data
                    if i >= len(matching_parlay.get('legs', [])):
                        continue
                    
                    processed_leg = matching_parlay['legs'][i]
                    
                    # Only process if game is final
                    if processed_leg.get('gameStatus') != 'STATUS_FINAL':
                        continue
                    
                    leg_updated = False
                    
                    # Update achieved_value from current stats
                    if processed_leg.get('current') is not None and bet_leg.achieved_value is None:
                        bet_leg.achieved_value = processed_leg['current']
                        leg_updated = True
                        app.logger.info(f"[AUTO-UPDATE] Bet {bet.id} Leg {i+1}: achieved_value = {processed_leg['current']}")
                    
                    # Update game status
                    if bet_leg.game_status != 'STATUS_FINAL':
                        bet_leg.game_status = 'STATUS_FINAL'
                        leg_updated = True
                    
                    # Update final scores
                    if processed_leg.get('homeScore') is not None:
                        bet_leg.home_score = processed_leg['homeScore']
                        bet_leg.away_score = processed_leg['awayScore']
                        leg_updated = True
                    
                    # Calculate and save leg status (won/lost) based on bet type
                    # Only update if status is pending AND is_hit is None (not already determined)
                    if bet_leg.status == 'pending' and bet_leg.is_hit is None and bet_leg.achieved_value is not None:
                        leg_status = 'lost'  # Default to lost
                        stat_type = bet_leg.bet_type.lower()
                        
                        if stat_type == 'moneyline':
                            # Moneyline: won if score_diff > 0
                            leg_status = 'won' if bet_leg.achieved_value > 0 else 'lost'
                        elif stat_type == 'spread':
                            # Spread: won if (score_diff + spread) > 0
                            if bet_leg.target_value is not None:
                                leg_status = 'won' if (bet_leg.achieved_value + bet_leg.target_value) > 0 else 'lost'
                        else:
                            # Player props: won if achieved_value >= target_value
                            if bet_leg.target_value is not None:
                                # Check for over/under
                                if bet_leg.bet_line_type == 'under':
                                    leg_status = 'won' if bet_leg.achieved_value < bet_leg.target_value else 'lost'
                                else:  # 'over' or None (default to over)
                                    leg_status = 'won' if bet_leg.achieved_value >= bet_leg.target_value else 'lost'
                    
                    bet_leg.status = leg_status
                    bet_leg.is_hit = True if leg_status == 'won' else False
                    leg_updated = True
                    app.logger.info(f"[AUTO-UPDATE] Bet {bet.id} Leg {i+1}: status = {leg_status}, is_hit = {bet_leg.is_hit}")
                
                if updated_legs > 0:
                    updated_bets += 1
                    
            except Exception as e:
                app.logger.error(f"[AUTO-UPDATE] Error updating bet {bet.id}: {e}")
                continue
        
        # Commit all updates
        if updated_legs > 0:
            db.session.commit()
            app.logger.info(f"[AUTO-UPDATE] ✓ Updated {updated_legs} legs across {updated_bets} bets")
        else:
            app.logger.info("[AUTO-UPDATE] No legs needed updating")
            
    except Exception as e:
        app.logger.error(f"[AUTO-UPDATE] Error in update_completed_bet_legs: {e}")
        db.session.rollback()

def normalize_bet_leg_team_names():
    """Normalize team names in bet_legs table on startup.
    
    Updates all bet_legs to use consistent team naming:
    - home_team: Uses nickname (e.g., "Lions", "Thunder") 
    - away_team: Uses nickname (e.g., "Bills", "Lakers")
    - player_team: Uses abbreviation (e.g., "DET", "OKC")
    
    SPORT-AWARE: Uses the sport column from bet_legs to match the correct sport's team
    
    Also updates status and is_hit for completed bets with pending legs.
    """
    try:
        from models import Team
        
        app.logger.info("[DATA-NORMALIZE] Starting SPORT-AWARE team name normalization...")
        
        # Build sport-specific lookup dictionaries from teams table
        teams = Team.query.all()
        
        # Separate lookups by sport: lookups[sport][lookup_type][key] = value
        lookups = {'NFL': {}, 'NBA': {}}
        
        for sport in ['NFL', 'NBA']:
            sport_teams = [t for t in teams if t.sport == sport]
            
            # Map: full name -> nickname (e.g., "Detroit Lions" -> "Lions")
            name_to_nickname = {}
            # Map: abbreviation -> nickname (e.g., "DET" -> "Lions" for NFL, "Pistons" for NBA)
            abbr_to_nickname = {}
            # Map: full name -> abbreviation (e.g., "Detroit Lions" -> "DET")
            name_to_abbr = {}
            # Map: nickname -> abbreviation (e.g., "Lions" -> "DET" for NFL)
            nickname_to_abbr = {}
            
            for team in sport_teams:
                if team.nickname:
                    # Full name mappings
                    if team.team_name:
                        name_to_nickname[team.team_name.lower().strip()] = team.nickname
                        name_to_abbr[team.team_name.lower().strip()] = team.team_abbr
                    
                    # Abbreviation mappings
                    if team.team_abbr:
                        abbr_to_nickname[team.team_abbr.upper().strip()] = team.nickname
                        nickname_to_abbr[team.nickname.lower().strip()] = team.team_abbr
                    
                    # Short name mappings (if different from nickname)
                    if team.team_name_short and team.team_name_short != team.nickname:
                        name_to_nickname[team.team_name_short.lower().strip()] = team.nickname
                        name_to_abbr[team.team_name_short.lower().strip()] = team.team_abbr
            
            lookups[sport] = {
                'name_to_nickname': name_to_nickname,
                'abbr_to_nickname': abbr_to_nickname,
                'name_to_abbr': name_to_abbr,
                'nickname_to_abbr': nickname_to_abbr
            }
        
        app.logger.info(f"[DATA-NORMALIZE] Built sport-specific lookup tables: NFL={len(lookups['NFL']['name_to_nickname'])}, NBA={len(lookups['NBA']['name_to_nickname'])}")
        
        # Helper function to normalize team name to nickname (sport-aware)
        def to_nickname(team_str, sport):
            if not team_str or not sport or sport not in lookups:
                return team_str
            
            sport_lookup = lookups[sport]
            team_lower = team_str.lower().strip()
            team_upper = team_str.upper().strip()
            
            # CRITICAL FIX: Check if this is a nickname/name/abbr from the WRONG sport
            # If so, we need to convert it to the correct sport's team
            # Example: "Timberwolves" (NBA) on NFL leg should become "Vikings" (NFL) - both MIN
            wrong_sport = 'NBA' if sport == 'NFL' else 'NFL'
            if wrong_sport in lookups:
                wrong_sport_lookup = lookups[wrong_sport]
                
                # Is this a nickname from the wrong sport?
                if team_lower in wrong_sport_lookup['nickname_to_abbr']:
                    # Get the abbreviation from wrong sport
                    abbr = wrong_sport_lookup['nickname_to_abbr'][team_lower]
                    # Look up the correct sport's team with same abbreviation
                    if abbr.upper() in sport_lookup['abbr_to_nickname']:
                        app.logger.info(f"[DATA-NORMALIZE] Converting {team_str} ({wrong_sport}) to {sport_lookup['abbr_to_nickname'][abbr.upper()]} ({sport}) via {abbr}")
                        return sport_lookup['abbr_to_nickname'][abbr.upper()]
            
            # Check if it's already a nickname in the correct sport
            if team_lower in sport_lookup['nickname_to_abbr']:
                return team_str  # Already normalized
            
            # Check if it's a full name
            if team_lower in sport_lookup['name_to_nickname']:
                return sport_lookup['name_to_nickname'][team_lower]
            
            # Check if it's an abbreviation
            if team_upper in sport_lookup['abbr_to_nickname']:
                return sport_lookup['abbr_to_nickname'][team_upper]
            
            # Try partial matching (e.g., "Los Angeles Lakers" contains "Lakers")
            for full_name, nickname in sport_lookup['name_to_nickname'].items():
                if full_name in team_lower or team_lower in full_name:
                    return nickname
            
            # No match found, return original
            return team_str
        
        # Helper function to normalize team name to abbreviation (sport-aware)
        def to_abbr(team_str, sport):
            if not team_str or not sport or sport not in lookups:
                return team_str
            
            sport_lookup = lookups[sport]
            team_lower = team_str.lower().strip()
            team_upper = team_str.upper().strip()
            
            # Check if it's already an abbreviation
            if team_upper in sport_lookup['abbr_to_nickname']:
                return team_upper  # Already normalized
            
            # Check if it's a nickname
            if team_lower in sport_lookup['nickname_to_abbr']:
                return sport_lookup['nickname_to_abbr'][team_lower]
            
            # Check if it's a full name
            if team_lower in sport_lookup['name_to_abbr']:
                return sport_lookup['name_to_abbr'][team_lower]
            
            # Try partial matching
            for full_name, abbr in sport_lookup['name_to_abbr'].items():
                if full_name in team_lower or team_lower in full_name:
                    return abbr
            
            # No match found, return original
            return team_str
        
        # Get all bet legs
        all_legs = BetLeg.query.all()
        app.logger.info(f"[DATA-NORMALIZE] Processing {len(all_legs)} bet legs...")
        
        updated_home = 0
        updated_away = 0
        updated_player_team = 0
        updated_status = 0
        updated_sport = 0
        
        for leg in all_legs:
            leg_updated = False
            
            # Determine sport - default to NFL if not set
            leg_sport = leg.sport if leg.sport else 'NFL'
            if not leg.sport:
                leg.sport = 'NFL'
                leg_updated = True
                updated_sport += 1
            
            # 1. Normalize home_team to nickname (sport-aware)
            if leg.home_team:
                normalized_home = to_nickname(leg.home_team, leg_sport)
                if normalized_home != leg.home_team:
                    leg.home_team = normalized_home
                    leg_updated = True
                    updated_home += 1
            
            # 2. Normalize away_team to nickname (sport-aware)
            if leg.away_team:
                normalized_away = to_nickname(leg.away_team, leg_sport)
                if normalized_away != leg.away_team:
                    leg.away_team = normalized_away
                    leg_updated = True
                    updated_away += 1
            
            # 3. Normalize player_team to abbreviation (sport-aware)
            if leg.player_team:
                normalized_team = to_abbr(leg.player_team, leg_sport)
                if normalized_team != leg.player_team:
                    leg.player_team = normalized_team
                    leg_updated = True
                    updated_player_team += 1
            
            # 4. Update status and is_hit for completed bets with pending legs
            # CRITICAL: Only update if BOTH status is pending AND is_hit is None
            # This prevents overwriting manually set or previously calculated results
            if leg.status == 'pending' and leg.is_hit is None:
                # Check if this leg's bet is completed (is_active=False)
                bet = leg.bet
                if bet and not bet.is_active and bet.status == 'completed':
                    # Only update if we have final game data
                    if leg.game_status == 'STATUS_FINAL' and leg.achieved_value is not None and leg.target_value is not None:
                        # Calculate won/lost based on bet type
                        stat_type = leg.bet_type.lower()
                        leg_status = 'lost'  # Default
                        
                        if stat_type == 'moneyline':
                            leg_status = 'won' if leg.achieved_value > 0 else 'lost'
                        elif stat_type == 'spread':
                            leg_status = 'won' if (leg.achieved_value + leg.target_value) > 0 else 'lost'
                        else:
                            # Player props
                            if leg.bet_line_type == 'under':
                                leg_status = 'won' if leg.achieved_value < leg.target_value else 'lost'
                            else:
                                leg_status = 'won' if leg.achieved_value >= leg.target_value else 'lost'
                        
                        if leg.status != leg_status:
                            leg.status = leg_status
                            leg_updated = True
                            updated_status += 1
                            app.logger.info(f"Set status={leg_status}, is_hit={leg.is_hit} for leg: {leg.player_name or leg.team}")
        
        # Commit all changes
        if updated_home > 0 or updated_away > 0 or updated_player_team > 0 or updated_status > 0 or updated_sport > 0:
            db.session.commit()
            app.logger.info(f"[DATA-NORMALIZE] ✓ Sport-aware normalization complete:")
            app.logger.info(f"  - sport: {updated_sport} legs defaulted to NFL")
            app.logger.info(f"  - home_team: {updated_home} legs updated to sport-specific nicknames")
            app.logger.info(f"  - away_team: {updated_away} legs updated to sport-specific nicknames")
            app.logger.info(f"  - player_team: {updated_player_team} legs updated to sport-specific abbreviations")
            app.logger.info(f"  - status/is_hit: {updated_status} legs updated for completed bets")
        else:
            app.logger.info("[DATA-NORMALIZE] No normalization needed - all data already consistent")
    
    except Exception as e:
        app.logger.error(f"[DATA-NORMALIZE] Error normalizing team names: {e}")
        db.session.rollback()

def backup_to_json(user_id=None):
    """Backup database bets to JSON files (for specific user or all)"""
    try:
        if user_id:
            user = User.query.get(user_id)
            if user:
                filename = f"user_{user.id}_{user.username}_bets.json"
                bets = get_user_bets_from_db(user_id)
                bets_data = [bet.get_bet_data() for bet in bets]
                with open(data_path(filename), 'w') as f:
                    json.dump(bets_data, f, indent=2)
        else:
            # Backup all users
            users = User.query.all()
            for user in users:
                backup_to_json(user.id)
    except Exception as e:
        app.logger.error(f"Error backing up to JSON: {e}")

def load_parlays():
    try:
        with open(data_path("Todays_Bets.json")) as f:
            return json.load(f)
    except Exception as e:
        app.logger.error("Failed to load today_parlays.json: %s", e)
        return []

def initialize_parlay_files():
    """Initialize and organize parlays into appropriate files before server starts"""
    try:
        # Load all parlays
        today_parlays = load_parlays()
        live_parlays = load_live_parlays()
        historical_parlays = load_historical_bets()
        
        # DEBUG: Log what we loaded
        app.logger.info(f"[INIT] Loaded {len(today_parlays)} from Todays_Bets.json")
        app.logger.info(f"[INIT] Loaded {len(live_parlays)} from Live_Bets.json")
        app.logger.info(f"[INIT] Loaded {len(historical_parlays)} from Historical_Bets.json")
        if live_parlays:
            app.logger.info(f"[INIT] Live parlays: {[p.get('name') for p in live_parlays]}")

        # Don't clear live parlays - we want to keep them and just check their status
        # live_parlays = []  # REMOVED: This was clearing live bets on every restart!

        # Create set of existing historical parlay IDs to prevent duplicates
        existing_historical = {f"{p['name']}_{p['legs'][0]['game_date']}" 
                             for p in historical_parlays if p.get('legs')}
        
        # Create set of existing live parlay IDs
        existing_live = {f"{p['name']}_{p['legs'][0]['game_date']}" 
                        for p in live_parlays if p.get('legs')}

        # Process each parlay from today's file
        new_today_parlays = []
        for parlay in today_parlays:
            if not parlay.get('legs'):
                continue

            # Check all legs to determine if parlay is complete or live
            all_games_complete = True
            any_game_active = False

            for leg in parlay['legs']:
                game_date = leg.get('game_date')
                if not game_date:
                    continue

                # Check game status regardless of date
                # Get game details to check if it's complete
                events = get_events(game_date)
                for event in events:
                    team_names = {c['team']['displayName'] for c in event['competitions'][0]['competitors']}
                    if leg['away'] in team_names and leg['home'] in team_names:
                        status = event['status']['type']['name']
                        if status == 'STATUS_FINAL':
                            continue
                        elif status == 'STATUS_IN_PROGRESS':
                            any_game_active = True
                            all_games_complete = False
                            break
                        else:
                            all_games_complete = False
                            break

                if not all_games_complete:
                    break

            # Create unique identifier for this parlay
            parlay_id = f"{parlay['name']}_{parlay['legs'][0]['game_date']}"

            # Ensure betting metadata fields exist on parlay
            parlay_odds = parlay.get('odds')
            parlay_wager = parlay.get('wager')
            # If the parlay contains a per-leg odds list, keep it
            leg_odds = [l.get('odds') for l in parlay.get('legs', []) if l.get('odds') is not None]

            # Add to appropriate list based on status
            if all_games_complete:
                if parlay_id not in existing_historical:
                    # compute returns if coming from today's
                    returns = parlay.get('returns')
                    # Treat None or empty-string as missing and compute
                    if returns is None or (isinstance(returns, str) and str(returns).strip() == ""):
                        returns = compute_parlay_returns_from_odds(parlay_wager, parlay_odds, leg_odds)
                        if returns is not None:
                            returns = f"{returns:.2f}"
                    parlay['returns'] = returns
                    historical_parlays.append(parlay)
            elif any_game_active:
                if parlay_id not in existing_live:
                    returns = parlay.get('returns')
                    if returns is None or (isinstance(returns, str) and str(returns).strip() == ""):
                        returns = compute_parlay_returns_from_odds(parlay_wager, parlay_odds, leg_odds)
                        if returns is not None:
                            returns = f"{returns:.2f}"
                    parlay['returns'] = returns
                    live_parlays.append(parlay)
            else:
                new_today_parlays.append(parlay)

        # Also check existing live parlays - they might have finished
        remaining_live_parlays = []
        for parlay in live_parlays:
            if not parlay.get('legs'):
                remaining_live_parlays.append(parlay)
                continue
            
            # Check if all games are complete
            all_games_complete = True
            for leg in parlay['legs']:
                game_date = leg.get('game_date')
                if not game_date:
                    continue
                
                events = get_events(game_date)
                for event in events:
                    team_names = {c['team']['displayName'] for c in event['competitions'][0]['competitors']}
                    if leg['away'] in team_names and leg['home'] in team_names:
                        status = event['status']['type']['name']
                        if status != 'STATUS_FINAL':
                            all_games_complete = False
                            break
                
                if not all_games_complete:
                    break
            
            # If complete, move to historical; otherwise keep in live
            parlay_id = f"{parlay['name']}_{parlay['legs'][0]['game_date']}"
            if all_games_complete and parlay_id not in existing_historical:
                historical_parlays.append(parlay)
            else:
                remaining_live_parlays.append(parlay)
        
        live_parlays = remaining_live_parlays

        # Sort all lists by date
        historical_parlays = sort_parlays_by_date(historical_parlays)
        live_parlays = sort_parlays_by_date(live_parlays)
        new_today_parlays = sort_parlays_by_date(new_today_parlays)

        # DON'T save files on initialization - files are the source of truth
        # Only save Historical and Todays if there were actual changes from processing
        # NEVER overwrite Live_Bets.json on startup - it should only be modified via API
        # save_parlays(historical_parlays, data_path("Historical_Bets.json"))
        # save_parlays(live_parlays, data_path("Live_Bets.json"))
        # save_parlays(new_today_parlays, data_path("Todays_Bets.json"))

        # Compute and persist any missing returns on startup (idempotent)
        try:
            res = compute_and_persist_returns(force=False)
            app.logger.info(f"Auto-computed returns on startup: {res}")
        except Exception as e:
            app.logger.error(f"Failed to auto-compute returns: {e}")

        return new_today_parlays
    except Exception as e:
        app.logger.error(f"Failed to initialize parlay files: {e}")
        return []

def load_live_parlays():
    try:
        with open(data_path("Live_Bets.json")) as f:
            return json.load(f)
    except Exception as e:
        app.logger.error("Failed to load live_parlays.json: %s", e)
        return []

def load_historical_bets():
    try:
        with open(data_path("Historical_Bets.json")) as f:
            return json.load(f)
    except Exception as e:
        app.logger.error("Failed to load historical_bets.json: %s", e)
        return []

def save_parlays(parlays, filename):
    try:
        # filename may be a full path or a simple name; ensure we write to Data dir
        path = filename
        # if a bare filename was passed, join with DATA_DIR
        if not os.path.isabs(path) and os.path.basename(path) == path:
            path = data_path(path)
        with open(path, "w") as f:
            json.dump(parlays, f, indent=2)
    except Exception as e:
        app.logger.error(f"Failed to save {filename}: {e}")

def sort_parlays_by_date(parlays):
    # Sort parlays by the most recent game date in any leg
    def get_latest_date(parlay):
        dates = [leg.get('game_date', '1900-01-01') for leg in parlay.get('legs', [])]
        return max(dates) if dates else '1900-01-01'
    return sorted(parlays, key=get_latest_date, reverse=True)

def process_parlays(current_parlays):
    """Process and sort parlays into appropriate files based on their status"""
    # Load existing parlays
    historical = load_historical_bets()
    live = []  # Reset live parlays as they will be rebuilt
    new_today_parlays = []
    
    # Create set of existing historical parlay identifiers
    existing_historical = {f"{p['name']}_{p['legs'][0]['game_date']}" 
                         for p in historical if p.get('legs')}
                         
    # Track IDs of parlays we're processing to avoid duplicates in live list
    processed_live = set()
    
    # Process each current parlay
    for parlay in current_parlays:
        if not parlay.get('legs'):
            continue
            
        # Create unique identifier for this parlay
        first_game_date = parlay['legs'][0].get('game_date')
        if not first_game_date:
            continue
            
        parlay_id = f"{parlay['name']}_{first_game_date}"
        
        # Skip if already in historical
        if parlay_id in existing_historical:
            continue
            
        # Skip if we've already processed this parlay into live list
        if parlay_id in processed_live:
            continue
        
        # Check all legs to determine if parlay is complete
        all_games_complete = True
        any_game_active = False
        
        for leg in parlay['legs']:
            game_date = leg.get('game_date')
            if not game_date:
                continue
                
            # Get game details to check if it's complete
            events = get_events(game_date)
            for event in events:
                team_names = {c['team']['displayName'] for c in event['competitions'][0]['competitors']}
                if leg['away'] in team_names and leg['home'] in team_names:
                    status = event['status']['type']['name']
                    if status == 'STATUS_FINAL':
                        continue
                    elif status == 'STATUS_IN_PROGRESS':
                        any_game_active = True
                        all_games_complete = False
                        break
                    else:
                        all_games_complete = False
                        break
            
            if not all_games_complete:
                break
        
        # Add to appropriate list based on game status
        if all_games_complete:
            # Add to historical if it's not already there
            if parlay_id not in existing_historical:
                # preserve odds/wager and compute returns if needed
                parlay_odds = parlay.get('odds')
                parlay_wager = parlay.get('wager')
                leg_odds = [l.get('odds') for l in parlay.get('legs', []) if l.get('odds') is not None]
                returns = parlay.get('returns')
                # Treat None or empty-string as missing and compute
                if returns is None or (isinstance(returns, str) and str(returns).strip() == ""):
                    returns = compute_parlay_returns_from_odds(parlay_wager, parlay_odds, leg_odds)
                    if returns is not None:
                        returns = f"{returns:.2f}"
                    parlay['returns'] = returns
                historical.append(parlay)
                existing_historical.add(parlay_id)
        elif any_game_active:
            # Add to live if we haven't processed it yet
            if parlay_id not in processed_live:
                parlay_odds = parlay.get('odds')
                parlay_wager = parlay.get('wager')
                leg_odds = [l.get('odds') for l in parlay.get('legs', []) if l.get('odds') is not None]
                returns = parlay.get('returns')
                # Treat None or empty-string as missing and compute
                if returns is None or (isinstance(returns, str) and str(returns).strip() == ""):
                    returns = compute_parlay_returns_from_odds(parlay_wager, parlay_odds, leg_odds)
                    if returns is not None:
                        returns = f"{returns:.2f}"
                    parlay['returns'] = returns
                live.append(parlay)
                processed_live.add(parlay_id)
        else:
            # Keep in today's parlays if it's not in historical or live
            if parlay_id not in existing_historical and parlay_id not in processed_live:
                new_today_parlays.append(parlay)
    
    # Sort all lists by date
    historical = sort_parlays_by_date(historical)
    live = sort_parlays_by_date(live)
    new_today_parlays = sort_parlays_by_date(new_today_parlays)
    
    # Save all files using the canonical/new naming convention
    save_parlays(historical, "Historical_Bets.json")
    save_parlays(live, "Live_Bets.json")
    save_parlays(new_today_parlays, "Todays_Bets.json")

    return new_today_parlays

def is_past_date(game_date_str):
    today = datetime.now().date()
    game_date = datetime.strptime(game_date_str, "%Y-%m-%d").date()
    return game_date < today

def get_events(date_str, sport='NFL'):
    """Fetch events from ESPN API for a given date and sport.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        sport: Sport code (NFL, NBA, MLB, NHL, etc.)
    """
    app.logger.info(f"Fetching {sport} events for date: {date_str}")
    # Mock data disabled - prefer real ESPN responses for accuracy. If you need
    # mock data for offline testing, re-enable or modify the block below.
    #
    # if date_str == "2025-10-13":
    #     app.logger.info("Using mock data for 2025-10-13")
    #     return mock_data
    
    # For other dates, try the real API
    d = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y%m%d")
    
    # Map sport codes to ESPN API paths
    sport_map = {
        'NFL': 'football/nfl',
        'NBA': 'basketball/nba',
        'MLB': 'baseball/mlb',
        'NHL': 'hockey/nhl',
        'NCAAF': 'football/college-football',
        'NCAAB': 'basketball/mens-college-basketball'
    }
    
    sport_path = sport_map.get(sport.upper(), 'football/nfl')
    url = f"http://site.api.espn.com/apis/site/v2/sports/{sport_path}/scoreboard?dates={d}"
    
    try:
        app.logger.info(f"Fetching from URL: {url}")
        data = requests.get(url).json()
        return data.get("events", [])
    except Exception as e:
        app.logger.error(f"Failed to fetch {sport} events for {date_str}: {e}")
        return []

def _get_player_stat_from_boxscore(player_name, category_name, stat_label, boxscore):
    """Get a specific stat for a player from the boxscore."""
    # Normalize names for more robust matching (remove punctuation, lower-case)
    def _norm(s):
        import re
        return re.sub(r"[^a-z0-9 ]+", "", s.lower()).strip()

    player_norm = _norm(player_name)
    for team_box in boxscore:
        for cat in team_box.get("statistics", []):
            if cat.get("name", "").lower() == category_name.lower():
                try:
                    labels = [l for l in cat.get("labels", [])]
                    if stat_label not in labels:
                        continue
                    stat_idx = labels.index(stat_label)
                    for ath in cat.get("athletes", []):
                        ath_name_raw = ath.get("athlete", {}).get("displayName", "")
                        ath_name = _norm(ath_name_raw)
                        # Match if all tokens of player_norm appear in athlete name
                        if all(tok in ath_name for tok in player_norm.split()):
                            stats = ath.get("stats", [])
                            if stat_idx < len(stats):
                                try:
                                    return int(float(stats[stat_idx]))
                                except Exception:
                                    return 0
                    # If strict token matching didn't find a player, try fuzzy matching
                    try:
                        import difflib
                        athlete_names = [a.get('athlete', {}).get('displayName', '') for a in cat.get('athletes', [])]
                        # find best match to player_name
                        matches = difflib.get_close_matches(player_name, athlete_names, n=1, cutoff=0.6)
                        if matches:
                            best = matches[0]
                            for ath in cat.get('athletes', []):
                                if ath.get('athlete', {}).get('displayName') == best:
                                    stats = ath.get('stats', [])
                                    if stat_idx < len(stats):
                                        try:
                                            return int(float(stats[stat_idx]))
                                        except Exception:
                                            return 0
                    except Exception:
                        pass
                except (ValueError, IndexError):
                    continue
    return 0

def _get_touchdowns(player_name, boxscore, scoring_plays=None):
    """Calculate total touchdowns for a player from boxscore and scoring_plays as fallback."""
    td_cats = {
        "rushing": "TD", "receiving": "TD",
        "interception": "TD", "kickoffReturn": "TD", "puntReturn": "TD",
        "fumbleReturn": "TD"
    }
    total_tds = 0
    # First try structured boxscore totals
    for cat, label in td_cats.items():
        total_tds += _get_player_stat_from_boxscore(player_name, cat, label, boxscore)

    # If we found any via boxscore, return that value
    if total_tds > 0:
        return total_tds

    # Otherwise try to parse scoring_plays (if provided) for touchdown entries
    if scoring_plays:
        import re
        def _norm(s):
            return re.sub(r"[^a-z0-9 ]+", "", (s or "").lower()).strip()

        player_norm = _norm(player_name)
        td_count = 0
        for play in scoring_plays:
            # Some play entries include participants with displayName fields
            participants = play.get("participants", [])
            for p in participants:
                name = p.get("displayName") or p.get("athlete", {}).get("displayName")
                if name and player_norm in _norm(name):
                    # He was part of a scoring play (likely a TD)
                    td_count += 1
                    break
        return td_count

    return total_tds

def calculate_bet_value(bet, game_data):
    """Calculate the current value for a bet based on game data."""
    stat = bet.get("stat", "").strip().lower() if bet.get("stat") else ""  # Normalize to lowercase for comparisons
    boxscore = game_data.get("boxscore", [])
    scoring_plays = game_data.get("scoring_plays", [])
    
    # --- Player Props ---
    if "player" in bet:
        player_name = bet["player"]
        
        # Simple Box Score Stats
        stat_map = {
            "passing_yards": ("passing", "YDS"), "passing_yards_alt": ("passing", "YDS"),
            "pass_attempts": ("passing", "ATT"),
            "pass_completions": ("passing", "COMP"), "passing_touchdowns": ("passing", "TD"),
            "interceptions_thrown": ("passing", "INT"), "longest_pass_completion": ("passing", "LONG"),
            "rushing_yards": ("rushing", "YDS"), "rushing_yards_alt": ("rushing", "YDS"),
            "rushing_attempts": ("rushing", "CAR"),
            "rushing_touchdowns": ("rushing", "TD"), "longest_rush": ("rushing", "LONG"),
            "receiving_yards": ("receiving", "YDS"), "receiving_yards_alt": ("receiving", "YDS"),
            "receptions": ("receiving", "REC"), "receptions_alt": ("receiving", "REC"),
            "receiving_touchdowns": ("receiving", "TD"), "longest_reception": ("receiving", "LONG"),
            "sacks": ("defensive", "SACK"), "tackles_assists": ("defensive", "TOT"),
            "field_goals_made": ("kicking", "FGM"), "kicking_points": ("kicking", "PTS"),
        }
        if stat in stat_map:
            cat, label = stat_map[stat]
            return _get_player_stat_from_boxscore(player_name, cat, label, boxscore)

        # Complex Player Stats
        if stat == "rushing_receiving_yards":
            rush = _get_player_stat_from_boxscore(player_name, "rushing", "YDS", boxscore)
            rec = _get_player_stat_from_boxscore(player_name, "receiving", "YDS", boxscore)
            return rush + rec
        
        if stat == "passing_rushing_yards":
            pass_yds = _get_player_stat_from_boxscore(player_name, "passing", "YDS", boxscore)
            rush_yds = _get_player_stat_from_boxscore(player_name, "rushing", "YDS", boxscore)
            return pass_yds + rush_yds
        
        if stat in ["anytime_touchdown", "anytime_td_scorer", "player_to_score_2_touchdowns", "player_to_score_3_touchdowns"]:
            return _get_touchdowns(player_name, boxscore, scoring_plays)

        td_plays = [p for p in scoring_plays if "Touchdown" in p.get("type", {}).get("text", "")]
        if stat == "first_touchdown_scorer":
            if td_plays and player_name.lower() in td_plays[0].get("participants", [{}])[0].get("displayName", "").lower():
                return 1
            return 0
        if stat == "last_touchdown_scorer":
            if td_plays and player_name.lower() in td_plays[-1].get("participants", [{}])[0].get("displayName", "").lower():
                return 1
            return 0

    # --- Team & Game Props ---
    home_score = game_data["score"]["home"]
    away_score = game_data["score"]["away"]
    
    if stat == "team_total_points":
        return home_score if bet["team"] == game_data["teams"]["home"] else away_score
    
    if stat == "total_points" or stat == "total_points_under" or stat == "total_points_over":
        return home_score + away_score

    if stat == "first_team_to_score":
        if scoring_plays:
            return scoring_plays[0].get("team", {}).get("displayName")
        return "N/A"

    if stat == "last_team_to_score":
        if scoring_plays:
            return scoring_plays[-1].get("team", {}).get("displayName")
        return "N/A"
        
    if stat == "will_be_overtime":
        return 1 if game_data.get("period", 0) > 4 else 0

    # --- Moneyline (Team to Win) ---
    if stat == "moneyline":
        # Requires "team" field in bet to specify which team to bet on
        if "team" not in bet:
            return 0
        
        bet_team = bet["team"]
        home_team = game_data["teams"]["home"]
        away_team = game_data["teams"]["away"]
        
        # Normalize team names for comparison (handle both abbreviations and full names)
        bet_team_norm = bet_team.lower().strip()
        home_team_norm = home_team.lower().strip()
        away_team_norm = away_team.lower().strip()
        
        # Calculate score differential from bet team's perspective
        # This shows if the team is winning (+) or losing (-)
        if (bet_team_norm == home_team_norm or 
            bet_team_norm in home_team_norm or 
            home_team_norm in bet_team_norm):
            score_diff = home_score - away_score
        elif (bet_team_norm == away_team_norm or 
              bet_team_norm in away_team_norm or 
              away_team_norm in bet_team_norm):
            score_diff = away_score - home_score
        else:
            return 0
        
        # Return score differential (positive = winning, negative = losing)
        return score_diff
    
    # --- Spread (Point Spread Betting) ---
    if stat == "spread":
        # Requires "team" field and "target" field (the spread value)
        # Example: team="Lions", target=-7 means Lions must win by more than 7
        # Example: team="Lions", target=7 means Lions can lose by up to 7 and still cover
        if "team" not in bet:
            return 0
        
        bet_team = bet["team"]
        home_team = game_data["teams"]["home"]
        away_team = game_data["teams"]["away"]
        spread = bet.get("target", 0)
        
        # Normalize team names for comparison (handle both abbreviations and full names)
        bet_team_norm = bet_team.lower().strip()
        home_team_norm = home_team.lower().strip()
        away_team_norm = away_team.lower().strip()
        
        # Calculate the score difference from bet team's perspective
        # Check if bet_team matches home_team (exact match or one contains the other)
        if (bet_team_norm == home_team_norm or 
            bet_team_norm in home_team_norm or 
            home_team_norm in bet_team_norm):
            score_diff = home_score - away_score
        elif (bet_team_norm == away_team_norm or 
              bet_team_norm in away_team_norm or 
              away_team_norm in bet_team_norm):
            score_diff = away_score - home_score
        else:
            return 0
        
        # For spread bets, return the score differential so frontend can show progress
        # The frontend can determine if the bet covers by checking: score_diff + spread > 0
        # For example: BUF -6.5 with score_diff=-13 shows Buffalo losing by 13 (not covering)
        return score_diff

    return 0 # Default for unhandled stats

def fetch_game_details_from_espn(game_date, away_team, home_team, sport='NFL'):
    """Fetch detailed game data for a single game.
    
    Args:
        game_date: Date string in YYYY-MM-DD format
        away_team: Away team name or abbreviation
        home_team: Home team name or abbreviation
        sport: Sport code (NFL, NBA, MLB, NHL, etc.)
    """
    try:
        app.logger.info(f"Fetching {sport} game details for {away_team} @ {home_team} on {game_date}")
        events = get_events(game_date, sport)
        app.logger.info(f"Found {len(events)} {sport} events for {game_date}")
        
        ev = None
        for event in events:
            try:
                competitors = event['competitions'][0]['competitors']
                # Get both full names and abbreviations
                team_names = {c['team']['displayName'] for c in competitors}
                team_abbrs = {c['team']['abbreviation'] for c in competitors}
                app.logger.info(f"Event teams: {team_names} | Abbreviations: {team_abbrs}")
                
                # Match by either full name or abbreviation
                away_match = away_team in team_names or away_team in team_abbrs
                home_match = home_team in team_names or home_team in team_abbrs
                
                if away_match and home_match:
                    ev = event
                    app.logger.info("Found matching event")
                    break
            except Exception as e:
                app.logger.error(f"Error processing event: {str(e)}")
                continue
                
        if not ev:
            # Reduce log level for old games - they won't be in ESPN's current events
            app.logger.debug(f"No matching event found for {away_team} @ {home_team}")
            return None

        comp = ev["competitions"][0]
        away = next(c for c in comp["competitors"] if c["homeAway"] == "away")
        home = next(c for c in comp["competitors"] if c["homeAway"] == "home")

        # Prefer boxscore players from the competition, but fall back to the
        # ESPN summary endpoint when boxscore is missing or empty.
        boxscore_players = []
        scoring_plays = []
        comp_box = comp.get("boxscore")
        if comp_box and isinstance(comp_box, dict):
            boxscore_players = comp_box.get("players") or []
        else:
            # Try fetching the summary endpoint which contains boxscore and scoringPlays
            try:
                # Map sport codes to ESPN API paths
                sport_map = {
                    'NFL': 'football/nfl',
                    'NBA': 'basketball/nba',
                    'MLB': 'baseball/mlb',
                    'NHL': 'hockey/nhl',
                    'NCAAF': 'football/college-football',
                    'NCAAB': 'basketball/mens-college-basketball'
                }
                sport_path = sport_map.get(sport.upper(), 'football/nfl')
                summary_url = f"http://site.api.espn.com/apis/site/v2/sports/{sport_path}/summary?event={ev['id']}"
                app.logger.info(f"Fetching {sport} summary for event {ev['id']}: {summary_url}")
                summary = requests.get(summary_url, timeout=8).json()
                # summary may use camelCase keys
                s_box = summary.get("boxscore") or summary.get("boxScore") or {}
                boxscore_players = s_box.get("players") or []
                scoring_plays = summary.get("scoringPlays") or summary.get("scoring_plays") or []
                app.logger.info(f"Summary fetched: box players={len(boxscore_players)}, scoring plays={len(scoring_plays)}")
            except Exception as e:
                app.logger.error(f"Error fetching {sport} summary for event {ev.get('id')}: {e}")

        game = {
            "espn_game_id": ev["id"],
            "teams": {
                "away": away["team"]["displayName"], 
                "home": home["team"]["displayName"],
                "away_abbr": away["team"].get("abbreviation", ""),
                "home_abbr": home["team"].get("abbreviation", "")
            },
            "startTime": ev.get("date", "").split("T")[1][:5] + " ET" if "T" in ev.get("date", "") else "",
            "startDateTime": ev.get("date", ""),  # Full ISO datetime for countdown calculations
            "game_date": game_date,
            "statusTypeName": ev["status"]["type"]["name"],
            "period": ev["status"].get("period", 0),
            "clock": ev["status"].get("displayClock", "00:00"),
            "score": {"away": int(away.get("score", 0)), "home": int(home.get("score", 0))},
            "boxscore": boxscore_players,
            "scoring_plays": scoring_plays,
            "leaders": []
        }
        return game

    except Exception as e:
        app.logger.error(f"Error in fetch_game_details_from_espn: {str(e)}")
        return None

game_data_cache = {}

def process_parlay_data(parlays):
    """Process a list of parlays with game data."""
    app.logger.info("Starting process_parlay_data")
    processed_parlays = []
    
    for parlay in parlays:
        app.logger.info(f"Processing parlay: {parlay.get('name')}")
        parlay_games = {}
        
        for leg in parlay.get("legs", []):
            app.logger.info(f"Processing leg for {leg.get('player')} - {leg.get('stat')}")
            sport = leg.get('sport', 'NFL')  # Default to NFL if not specified
            game_key = f"{leg['game_date']}_{sport}_{leg['away']}_{leg['home']}"
            app.logger.info(f"Game key: {game_key}")
            
            if game_key not in game_data_cache:
                app.logger.info(f"Fetching {sport} game data for {game_key}")
                game_data = fetch_game_details_from_espn(leg['game_date'], leg['away'], leg['home'], sport)
                app.logger.info(f"Game data fetched: {game_data is not None}")
                game_data_cache[game_key] = game_data
            else:
                app.logger.info(f"Using cached game data for {game_key}")
            
            if game_data_cache.get(game_key):
                app.logger.info(f"Adding game data to parlay_games: {game_key}")
                parlay_games[game_key] = game_data_cache[game_key]
            else:
                # Reduce log level for historical games without live data
                app.logger.debug(f"No game data available for {game_key}")

        for leg in parlay.get("legs", []):
            app.logger.info(f"Processing leg in final stage: {leg}")
            sport = leg.get('sport', 'NFL')  # Get sport for this leg
            game_key = f"{leg['game_date']}_{sport}_{leg['away']}_{leg['home']}"
            game_data = parlay_games.get(game_key)
            app.logger.info(f"Game data for {game_key}: {game_data is not None}")
            
            leg["parlay_name"] = parlay.get("name", "Unknown Bet")

            if game_data:
                try:
                    # Update leg with live scores from game_data
                    home_score = game_data.get("score", {}).get("home", 0)
                    away_score = game_data.get("score", {}).get("away", 0)
                    leg["homeScore"] = home_score
                    leg["awayScore"] = away_score
                    
                    # Update leg with full team names from game_data
                    game_teams = game_data.get("teams", {})
                    if game_teams.get("away"):
                        leg["away"] = game_teams["away"]
                        leg["awayTeam"] = game_teams["away"]
                    if game_teams.get("home"):
                        leg["home"] = game_teams["home"]
                        leg["homeTeam"] = game_teams["home"]
                    
                    # Update leg with game status (scheduled, in_progress, final, etc.)
                    game_status = game_data.get("statusTypeName", "")
                    if game_status:
                        leg["gameStatus"] = game_status
                    
                    app.logger.info(f"Updated scores: {leg.get('away')} {away_score} @ {leg.get('home')} {home_score} - Status: {game_status}")
                    
                    leg["current"] = calculate_bet_value(leg, game_data)
                    app.logger.info(f"Calculated value for {leg.get('player', leg.get('team', 'Unknown'))} - {leg['stat']}: {leg['current']}")
                    
                    # Add score differential for spread/moneyline bets
                    if leg["stat"] in ["spread", "moneyline"]:
                        home_team = game_data.get("teams", {}).get("home", "")
                        away_team = game_data.get("teams", {}).get("away", "")
                        
                        # Calculate from bet team's perspective
                        bet_team = leg.get("team", "")
                        
                        # Normalize team names for comparison (case-insensitive, strip whitespace)
                        bet_team_norm = (bet_team or "").lower().strip()
                        home_team_norm = (home_team or "").lower().strip()
                        away_team_norm = (away_team or "").lower().strip()
                        
                        # Also check if one team name contains the other (e.g., "LA Chargers" vs "Los Angeles Chargers")
                        if bet_team_norm == home_team_norm or bet_team_norm in home_team_norm or home_team_norm in bet_team_norm:
                            leg["score_diff"] = home_score - away_score
                            app.logger.info(f"Matched home team: '{bet_team}' == '{home_team}', score_diff = {home_score - away_score}")
                        elif bet_team_norm == away_team_norm or bet_team_norm in away_team_norm or away_team_norm in bet_team_norm:
                            leg["score_diff"] = away_score - home_score
                            app.logger.info(f"Matched away team: '{bet_team}' == '{away_team}', score_diff = {away_score - home_score}")
                        else:
                            leg["score_diff"] = 0
                            app.logger.warning(f"NO MATCH for team '{bet_team}' - ESPN has home:'{home_team}' away:'{away_team}'")
                            
                except Exception as e:
                    app.logger.error(f"Error calculating bet value: {str(e)}")
                    leg["current"] = 0
            else:
                # Reduce log level for historical games - expected for old completed bets
                app.logger.debug(f"No game data found for {game_key}")
                leg["current"] = 0

        # Copy all original parlay fields and add games
        processed_parlay = parlay.copy()
        processed_parlay["games"] = list(parlay_games.values())
        processed_parlays.append(processed_parlay)
    
    return processed_parlays

def update_live_bet_legs():
    """Background job to update live bet legs with real-time ESPN data.
    
    Finds all live/pending bets and updates their legs with current game data:
    - Fetches live scores from ESPN API
    - Updates current values for active bets
    - Keeps live bets showing real-time data
    
    This runs every minute during active game times.
    """
    try:
        app.logger.info("[LIVE-UPDATE] Starting live bet leg update check...")
        
        # Get all live and pending bets
        live_bets = Bet.query.filter(Bet.status.in_(['live', 'pending'])).all()
        
        if not live_bets:
            app.logger.info("[LIVE-UPDATE] No live/pending bets found")
            return
        
        app.logger.info(f"[LIVE-UPDATE] Updating {len(live_bets)} live/pending bets")
        
        updated_bets = 0
        updated_legs = 0
        
        for bet in live_bets:
            try:
                # Get bet data with live data fetching
                bet_data = bet.to_dict_structured(use_live_data=True)
                
                # Process the bet data to get live updates
                processed_bets = process_parlay_data([bet_data])
                
                if processed_bets and len(processed_bets) > 0:
                    processed_bet = processed_bets[0]
                    
                    # Update bet legs in database with live data
                    for leg_data in processed_bet.get('legs', []):
                        # Find corresponding bet leg in database
                        bet_leg = db.session.query(BetLeg).filter(
                            BetLeg.bet_id == bet.id,
                            BetLeg.leg_order == leg_data.get('leg_order', 0)
                        ).first()
                        
                        if bet_leg and 'current' in leg_data:
                            # Update current value if it changed
                            new_current = leg_data.get('current')
                            if new_current is not None and bet_leg.current_value != new_current:
                                bet_leg.current_value = float(new_current)
                                updated_legs += 1
                                app.logger.debug(f"[LIVE-UPDATE] Bet {bet.id} Leg {bet_leg.leg_order}: current_value = {new_current}")
                            
                            # Update game status if available
                            if 'gameStatus' in leg_data and leg_data['gameStatus']:
                                if bet_leg.game_status != leg_data['gameStatus']:
                                    bet_leg.game_status = leg_data['gameStatus']
                                    app.logger.debug(f"[LIVE-UPDATE] Bet {bet.id} Leg {bet_leg.leg_order}: game_status = {leg_data['gameStatus']}")
                            
                            # Update scores if available
                            if 'homeScore' in leg_data and leg_data['homeScore'] is not None:
                                bet_leg.home_score = int(leg_data['homeScore'])
                            if 'awayScore' in leg_data and leg_data['awayScore'] is not None:
                                bet_leg.away_score = int(leg_data['awayScore'])
                    
                    updated_bets += 1
                    
            except Exception as e:
                app.logger.error(f"[LIVE-UPDATE] Error updating live bet {bet.id}: {e}")
                continue
        
        # Commit all changes
        db.session.commit()
        
        if updated_legs > 0:
            app.logger.info(f"[LIVE-UPDATE] ✓ Updated {updated_legs} legs across {updated_bets} live bets")
        else:
            app.logger.info("[LIVE-UPDATE] No live bet legs needed updating")
            
    except Exception as e:
        app.logger.error(f"[LIVE-UPDATE] Error in update_live_bet_legs: {e}")
        db.session.rollback()

# Schedule automated tasks
scheduler.add_job(
    func=update_completed_bet_legs,
    trigger=IntervalTrigger(minutes=30),
    id='completed_bet_leg_updates',
    name='Update completed bet legs with final results every 30 minutes'
)

scheduler.add_job(
    func=update_live_bet_legs,
    trigger=IntervalTrigger(minutes=1),
    id='live_bet_updates',
    name='Update live bet legs with real-time data every minute'
)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)