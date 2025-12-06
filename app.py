print("DEBUG: app.py imported")
from services import compute_and_persist_returns
# Define run_migrations_once before usage
from flask import Flask, jsonify, send_from_directory, request, session
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import requests
import os
import time
import json
import logging
import atexit
from datetime import datetime, timedelta, date

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# DISABLED: SQL query logging - too verbose for production, use only for local debugging
# sql_logger = logging.getLogger('sqlalchemy.engine')
# sql_logger.setLevel(logging.WARNING)  # Set to INFO to log queries, WARNING to disable



# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Import database models
from models import db, User, Bet, BetLeg, Player
from helpers.database import has_complete_final_data, save_final_results_to_bet, auto_move_completed_bets, auto_move_pending_to_live
from helpers.enhanced_player_search import enhanced_player_search
from flask_migrate import Migrate

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
@app.route('/admin/players')
def admin_players():
    """Admin dashboard for players with missing data"""
    incomplete_players = Player.query.filter(
        (Player.position == None) | 
        (Player.jersey_number == None) | 
        (Player.current_team == None) | 
        (Player.current_team == '')
    ).all()
    return render_template('admin_players.html', players=incomplete_players)

@app.route('/admin/players/enrich/<int:player_id>', methods=['POST'])
def admin_enrich_player(player_id):
    """Manually trigger enrichment for a player"""
    from jobs.player_enrichment_job import enrich_player_data
    # We'll just run the full job for simplicity, or we could target one.
    # For now, let's just re-run the job logic for this specific player
    # But since the job is robust, triggering the full job is fine too, 
    # or we can just call the search logic here.
    
    player = Player.query.get_or_404(player_id)
    try:
        from helpers.enhanced_player_search import enhanced_player_search
        sport = "football" if player.sport == 'NFL' else "basketball"
        league = "nfl" if player.sport == 'NFL' else "nba"
        
        data = enhanced_player_search(player.player_name, sport=sport, league=league)
        
        if data:
            if player.sport != data['sport']:
                player.sport = data['sport']
            if data['position']:
                player.position = data['position']
            if data['jersey_number']:
                try:
                    player.jersey_number = int(data['jersey_number'])
                except:
                    pass
            if data['current_team']:
                player.current_team = data['current_team']
            if data['team_abbreviation']:
                player.team_abbreviation = data['team_abbreviation']
            if data['espn_player_id']:
                player.espn_player_id = data['espn_player_id']
                
            db.session.commit()
            flash(f"Successfully enriched {player.player_name}", "success")
        else:
            flash(f"No data found for {player.player_name}", "warning")
            
    except Exception as e:
        db.session.rollback()
        flash(f"Error enriching player: {e}", "error")
        
    return redirect(url_for('admin_players'))

@app.route('/admin/players/delete/<int:player_id>', methods=['POST'])
def admin_delete_player(player_id):
    """Delete a player record"""
    player = Player.query.get_or_404(player_id)
    try:
        db.session.delete(player)
        db.session.commit()
        flash(f"Deleted {player.player_name}", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting player: {e}", "error")
    return redirect(url_for('admin_players'))

@app.route('/manifest.json')
def manifest():
    return app.send_static_file('manifest.json')

# Serve uncharted territories page
@app.route('/explore')
@app.route('/watched')
@app.route('/social')
def uncharted():
    return app.send_static_file('uncharted.html')

# Serve modern account page
@app.route('/account')
def account():
    return app.send_static_file('account.html')

# Serve issues page
@app.route('/issues')
def issues():
    return app.send_static_file('issues.html')

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
    # Only enable SSL if not in development mode (Docker)
    if os.environ.get('FLASK_ENV') != 'development':
        if '?' in database_url:
            database_url += '&sslmode=require'
        else:
            database_url += '?sslmode=require'
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
print(f"DEBUG: DATABASE_URL = {database_url}")
if 'sqlite' in database_url:
    print("DEBUG: Configuring for SQLite")
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {}
else:
    print("DEBUG: Configuring for PostgreSQL")
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

print("DEBUG: Initializing CORS")
CORS(app, supports_credentials=True)
print("DEBUG: Initializing DB")
db.init_app(app)
print(f"DEBUG: DB initialized. Extensions: {app.extensions.keys()}")
migrate = Migrate(app, db)

# Create database tables
# db.create_all() removed for Flask-Migrate

from functools import wraps
from helpers.utils import (
    compute_parlay_returns_from_odds,
    sort_parlays_by_date,
    get_events,
    _get_player_stat_from_boxscore,
    _get_touchdowns
)

from services import calculate_bet_value, process_parlay_data

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
    # Query bets where user is primary, secondary bettor, or watcher
    # SQLite workaround: Check string containment for JSON arrays
    user_id_str = str(user.id)
    query = Bet.query.filter(
        or_(
            Bet.user_id == user.id,  # Primary bettor
            # Check if user_id is in the JSON string (e.g. "[1, 2]")
            # We check for: "[1", ", 1,", "1]" to avoid matching 11 in [11]
            # But for simplicity in dev, simple string check is often enough, 
            # though strictly we should be careful. 
            # Let's use a slightly safer CAST to string approach if possible, 
            # or just rely on the fact that IDs are unique enough.
            # Actually, let's just use CAST to String and LIKE for now.
            db.cast(Bet.secondary_bettors, db.String).like(f'%{user_id_str}%'),
            db.cast(Bet.watchers, db.String).like(f'%{user_id_str}%')
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
# run_migrations_once(app) # Removed in favor of Flask-Migrate

from helpers.utils import data_path, DATA_DIR

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# app = Flask(__name__) removed (duplicate)

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
    from models import Team
    
    bet_legs = db.session.query(BetLeg).filter(
        BetLeg.bet_id == bet.id,
        BetLeg.game_date.isnot(None),
        ((BetLeg.game_id.is_(None) | (BetLeg.game_id == '')) | 
         (BetLeg.away_team.is_(None) | (BetLeg.away_team == 'TBD')))
    ).all()
    
    if not bet_legs:
        return  # No legs need game ID population
    
    app.logger.info(f"[GAME-ID-POPULATION] Populating game IDs for {len(bet_legs)} legs in bet {bet.id}")
    
    # Build team lookup from database (for normalization)
    teams = Team.query.all()
    team_lookup_for_norm = {}
    for sport in ['NFL', 'NBA', 'MLB', 'NHL']:
        sport_teams = [t for t in teams if t.sport == sport]
        abbr_to_fullname = {}
        shortname_to_fullname = {}
        for team in sport_teams:
            if team.team_name:
                full_name_norm = team.team_name.lower().strip()
                if team.team_abbr:
                    abbr_to_fullname[team.team_abbr.upper().strip()] = full_name_norm
                if team.team_name_short:
                    shortname_to_fullname[team.team_name_short.lower().strip()] = full_name_norm
                # Also add nickname mapping
                if team.nickname and team.nickname.lower().strip() != team.team_name.lower().strip():
                    shortname_to_fullname[team.nickname.lower().strip()] = full_name_norm
        team_lookup_for_norm[sport] = {
            'abbr_to_fullname': abbr_to_fullname,
            'shortname_to_fullname': shortname_to_fullname
        }
    
    def normalize_team_name_for_matching(team_str, sport='NFL'):
        """Normalize team name to ESPN-compatible full name for matching"""
        if not team_str or sport not in team_lookup_for_norm:
            return team_str.lower().strip() if team_str else ''
        
        lookup = team_lookup_for_norm[sport]
        team_lower = team_str.lower().strip()
        team_upper = team_str.upper().strip()
        
        # Try abbreviation lookup (e.g., "SEA" -> "seattle seahawks")
        if team_upper in lookup['abbr_to_fullname']:
            return lookup['abbr_to_fullname'][team_upper]
        
        # Try short name/nickname lookup (e.g., "Seahawks" -> "seattle seahawks")
        if team_lower in lookup['shortname_to_fullname']:
            return lookup['shortname_to_fullname'][team_lower]
        
        # Try partial match
        for shortname, fullname in lookup['shortname_to_fullname'].items():
            if shortname in team_lower:
                return fullname
        
        # Fallback: just return lowercase
        return team_lower
    
    # Group legs by game date for efficiency
    legs_by_date = {}
    for leg in bet_legs:
        date_key = leg.game_date
        if date_key not in legs_by_date:
            legs_by_date[date_key] = []
        legs_by_date[date_key].append(leg)
    
    # Process each date and up to 2 days into the future
    from datetime import timedelta
    for game_date, legs in legs_by_date.items():
        try:
            # Collect games from the game date + 2 days into future (for multi-day parlays)
            all_games = []
            for day_offset in range(3):  # 0, 1, 2 days from game_date
                search_date = game_date + timedelta(days=day_offset)
                games = get_espn_games_with_ids_for_date(search_date)
                if games:
                    all_games.extend(games)
                    app.logger.info(f"[GAME-ID-POPULATION] Found {len(games)} games for {search_date}")
            
            if not all_games:
                app.logger.warning(f"[GAME-ID-POPULATION] No games found for date range {game_date} to {game_date + timedelta(days=2)}")
                continue
            
            # Create lookup maps for faster matching
            # Store game data: list of (game_id, espn_away, espn_home, game_date)
            # We use a list because teams can play multiple games in the 3-day window (e.g. NBA back-to-back)
            game_lookup_both = {}  # (away_norm, home_norm) -> List[game_data]
            game_lookup_single_home = {}  # home_norm -> List[game_data]
            game_lookup_single_away = {}  # away_norm -> List[game_data]
            
            for game_id, espn_away, espn_home, g_date in all_games:
                # Normalize team names for matching
                away_norm = espn_away.lower().strip()
                home_norm = espn_home.lower().strip()
                game_data = (game_id, espn_away, espn_home, g_date)
                
                # Both teams lookup
                key = f"{away_norm}@{home_norm}"
                if key not in game_lookup_both: game_lookup_both[key] = []
                game_lookup_both[key].append(game_data)
                
                reverse_key = f"{home_norm}@{away_norm}"
                if reverse_key not in game_lookup_both: game_lookup_both[reverse_key] = []
                game_lookup_both[reverse_key].append(game_data)
                
                # Single team lookups (for TBD cases)
                if home_norm not in game_lookup_single_home: game_lookup_single_home[home_norm] = []
                game_lookup_single_home[home_norm].append(game_data)
                
                if away_norm not in game_lookup_single_away: game_lookup_single_away[away_norm] = []
                game_lookup_single_away[away_norm].append(game_data)
            
            def find_best_game_match(potential_games, target_date):
                """Find the best game match based on date proximity"""
                if not potential_games:
                    return None
                
                # Priority 1: Exact date match
                for g in potential_games:
                    game_date_obj = g[3]
                    # Handle both datetime and date objects
                    if hasattr(game_date_obj, 'date'):
                        game_date_val = game_date_obj.date()
                    else:
                        game_date_val = game_date_obj
                        
                    if game_date_val == target_date:
                        return g
                
                # Priority 2: Closest date match
                # Sort by absolute difference in days
                def get_date_diff(x):
                    d_obj = x[3]
                    if hasattr(d_obj, 'date'):
                        d_val = d_obj.date()
                    else:
                        d_val = d_obj
                    return abs((d_val - target_date).days)
                    
                sorted_games = sorted(potential_games, key=get_date_diff)
                return sorted_games[0]

            # Match each leg to a game
            for leg in legs:
                leg_needs_update = (not leg.game_id or leg.game_id == '') or (not leg.away_team or leg.away_team == 'TBD')
                
                if not leg_needs_update:  # Already has both game_id and away_team
                    continue
                
                # Normalize leg team names for matching
                leg_home_norm = normalize_team_name_for_matching(leg.home_team, leg.sport or 'NFL')
                leg_away_norm = normalize_team_name_for_matching(leg.away_team, leg.sport or 'NFL')
                
                # Normalize player team if available
                leg_player_team_norm = ''
                if leg.player_team:
                    leg_player_team_norm = normalize_team_name_for_matching(leg.player_team, leg.sport or 'NFL')
                
                app.logger.info(f"[GAME-ID-POPULATION] Leg {leg.id}: Matching '{leg.home_team}' (norm: '{leg_home_norm}') @ '{leg.away_team}' (norm: '{leg_away_norm}') | Player Team: '{leg.player_team}' (norm: '{leg_player_team_norm}')")
                
                # Try to match using player team if available (High Priority for OCR bets where teams might be TBD)
                if leg_player_team_norm and leg_player_team_norm != 'tbd':
                    # Check if player team matches any home team
                    if leg_player_team_norm in game_lookup_single_home:
                        match = find_best_game_match(game_lookup_single_home[leg_player_team_norm], leg.game_date)
                        if match:
                            game_id, espn_away, espn_home, _ = match
                            leg.game_id = game_id
                            leg.away_team = espn_away
                            leg.home_team = espn_home
                            app.logger.info(f"[GAME-ID-POPULATION] Set game_id {leg.game_id} for leg {leg.id} using player_team '{leg.player_team}' (matched as home)")
                            continue
                        
                    # Check if player team matches any away team
                    if leg_player_team_norm in game_lookup_single_away:
                        match = find_best_game_match(game_lookup_single_away[leg_player_team_norm], leg.game_date)
                        if match:
                            game_id, espn_away, espn_home, _ = match
                            leg.game_id = game_id
                            leg.away_team = espn_away
                            leg.home_team = espn_home
                            app.logger.info(f"[GAME-ID-POPULATION] Set game_id {leg.game_id} for leg {leg.id} using player_team '{leg.player_team}' (matched as away)")
                            continue
                
                # Skip if both teams are missing or TBD
                if (not leg.home_team or leg.home_team.lower().strip() == 'tbd') and \
                   (not leg.away_team or leg.away_team.lower().strip() == 'tbd'):
                    app.logger.warning(f"[GAME-ID-POPULATION] Skipping leg {leg.id}: both teams are TBD")
                    continue
                
                # Try to match on both teams if available
                if leg_home_norm != 'tbd' and leg_away_norm != 'tbd':
                    key = f"{leg_away_norm}@{leg_home_norm}"
                    if key in game_lookup_both:
                        match = find_best_game_match(game_lookup_both[key], leg.game_date)
                        if match:
                            game_id, espn_away, espn_home, _ = match
                            leg.game_id = game_id
                            leg.away_team = espn_away
                            leg.home_team = espn_home
                            app.logger.info(f"[GAME-ID-POPULATION] Set game_id {leg.game_id} for leg {leg.id}, teams: {leg.away_team} @ {leg.home_team}")
                            continue
                
                # Try to match on single team if other is TBD
                if leg_home_norm != 'tbd' and (not leg.away_team or leg.away_team.lower().strip() == 'tbd'):
                    if leg_home_norm in game_lookup_single_home:
                        match = find_best_game_match(game_lookup_single_home[leg_home_norm], leg.game_date)
                        if match:
                            game_id, espn_away, espn_home, _ = match
                            leg.game_id = game_id
                            leg.away_team = espn_away
                            leg.home_team = espn_home
                            app.logger.info(f"[GAME-ID-POPULATION] Set game_id {leg.game_id} for leg {leg.id}, matched home team: {leg.home_team}")
                            continue
                    if leg_home_norm in game_lookup_single_away:
                        match = find_best_game_match(game_lookup_single_away[leg_home_norm], leg.game_date)
                        if match:
                            game_id, espn_away, espn_home, _ = match
                            leg.game_id = game_id
                            leg.away_team = espn_away
                            leg.home_team = espn_home
                            app.logger.info(f"[GAME-ID-POPULATION] Set game_id {leg.game_id} for leg {leg.id}, matched as away team: {leg.away_team}")
                            continue
                
                if leg_away_norm != 'tbd' and (not leg.home_team or leg.home_team.lower().strip() == 'tbd'):
                    if leg_away_norm in game_lookup_single_away:
                        match = find_best_game_match(game_lookup_single_away[leg_away_norm], leg.game_date)
                        if match:
                            game_id, espn_away, espn_home, _ = match
                            leg.game_id = game_id
                            leg.away_team = espn_away
                            leg.home_team = espn_home
                            app.logger.info(f"[GAME-ID-POPULATION] Set game_id {leg.game_id} for leg {leg.id}, matched away team: {leg.away_team}")
                            continue
                    if leg_away_norm in game_lookup_single_home:
                        match = find_best_game_match(game_lookup_single_home[leg_away_norm], leg.game_date)
                        if match:
                            game_id, espn_away, espn_home, _ = match
                            leg.game_id = game_id
                            leg.away_team = espn_away
                            leg.home_team = espn_home
                            app.logger.info(f"[GAME-ID-POPULATION] Set game_id {leg.game_id} for leg {leg.id}, matched as home team: {leg.home_team}")
                            continue
                
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
    """Populate player_id and player_position for all bet legs in a bet.
    
    Skips:
    - Team moneyline/spread bets (where player_name is null)
    - Game total bets (where player_name is 'Game Total')
    - Legs that already have player_id
    """
    from helpers.espn_api import search_espn_player
    from models import Player
    
    # Filter for legs that need player population
    # Skip: team bets (player_name is None), game totals, and already-processed legs
    bet_legs = db.session.query(BetLeg).filter(
        BetLeg.bet_id == bet.id,
        BetLeg.player_name.isnot(None),  # Skip None (team bets, game totals)
        BetLeg.player_name != 'Unknown',  # Skip unknown
        BetLeg.player_name != 'Game Total',  # Skip game totals
        BetLeg.player_id.is_(None)  # Skip already processed
    ).all()
    
    if not bet_legs:
        return  # No legs need player data population
    
    app.logger.info(f"[PLAYER-POPULATION] Populating player data for {len(bet_legs)} legs in bet {bet.id}")
    
    # Expanded list of team identifiers
    team_identifiers = [
        # NFL
        'raiders', 'cowboys', 'chiefs', 'chargers', 'broncos', 'patriots', 'jets', 'giants', 'eagles', 'commanders', 
        'bears', 'lions', 'packers', 'vikings', 'falcons', 'panthers', 'saints', 'buccaneers', 'cardinals', 'rams', 
        '49ers', 'seahawks', 'bengals', 'browns', 'steelers', 'ravens', 'bills', 'dolphins', 'texans', 'colts', 
        'jaguars', 'titans',
        # NBA
        'lakers', 'celtics', 'warriors', 'bulls', 'heat', 'knicks', 'nets', 'sixers', 'raptors', 'bucks', 'suns', 
        'nuggets', 'clippers', 'mavericks', 'thunder', 'jazz', 'blazers', 'kings', 'wizards', 'hornets', 'pelicans', 
        'grizzlies', 'hawks', 'cavaliers', 'pistons', 'pacers', 'magic', 'spurs', 'rockets', 'timberwolves',
        # MLB
        'yankees', 'redsox', 'orioles', 'rays', 'bluejays', 'indians', 'guardians', 'twins', 'whitesox', 'royals', 
        'tigers', 'athletics', 'mariners', 'rangers', 'astros', 'angels', 'dodgers', 'padres', 'giants', 'rockies', 
        'braves', 'mets', 'nationals', 'marlins', 'phillies', 'cubs', 'cardinals', 'brewers', 'pirates', 'reds',
        # NHL
        'rangers', 'bruins', 'maple leafs', 'canadiens', 'devils', 'flyers', 'penguins', 'sabres', 'red wings', 
        'lightning', 'hurricanes', 'capitals', 'panthers', 'islanders', 'stars', 'avalanche', 'wild', 'blues', 
        'jets', 'blackhawks', 'canucks', 'flames', 'oilers', 'ducks', 'sharks', 'kings', 'kraken', 'golden knights', 'predators',
        # Generic
        'team', 'total', 'over', 'under', 'game'
    ]

    for leg in bet_legs:
        # SAFEGUARD: Skip player search for team props (moneyline, spread, totals, etc.)
        # These bets are team-based, so "player_name" is actually a team name.
        # Searching for them as players leads to incorrect fuzzy matches (e.g. "49ers" -> "Fred Warner")
        is_team_prop = False
        
        # Check bet_type
        if leg.bet_type and leg.bet_type.lower() in ['moneyline', 'spread', 'game_line', 'parlay', 'sgp']:
             # Definitive team props
             if leg.bet_type.lower() in ['moneyline', 'spread', 'game_line']:
                 is_team_prop = True
        
        # Check for ambiguous types (total, over_under, team_total)
        # Only treat as team prop if player_name matches a team identifier
        if leg.bet_type and leg.bet_type.lower() in ['total', 'over_under', 'team_total']:
            player_name_lower = leg.player_name.lower().strip() if leg.player_name else ""
            if any(team in player_name_lower for team in team_identifiers):
                is_team_prop = True
                app.logger.info(f"[PLAYER-POPULATION] Detected team name in player_name '{leg.player_name}' for bet_type '{leg.bet_type}' - treating as team prop")
            
        # Check stat_type (definitive for team props)
        if leg.stat_type and leg.stat_type.lower() in ['moneyline', 'spread', 'total_points', 'over_under', 'team_total_points', 'point_spread', 'total']:
             # Double check if it's a player prop disguised as a total (e.g. "Total Points" for a player)
             # If it's "Total Points" but has a player name that is NOT a team, it's a player prop
             if leg.stat_type.lower() in ['total_points', 'total']:
                 player_name_lower = leg.player_name.lower().strip() if leg.player_name else ""
                 if any(team in player_name_lower for team in team_identifiers):
                     is_team_prop = True
             else:
                 is_team_prop = True
            
        # Check if player_name is actually a team name (Catch-all)
        # This is critical for OCR bets where "Rams" might be extracted as the player
        player_name_lower = leg.player_name.lower().strip() if leg.player_name else ""
        
        if not is_team_prop and any(team in player_name_lower for team in team_identifiers):
            # Only set if we haven't already determined it's a player prop (though logic above is mostly inclusive)
            # Actually, if it matches a team identifier, it's almost certainly a team prop or we shouldn't search for it as a player
            is_team_prop = True
            app.logger.info(f"[PLAYER-POPULATION] Detected team name in player_name '{leg.player_name}' - treating as team prop")

        if is_team_prop:
            app.logger.info(f"[PLAYER-POPULATION] Skipping player search for team prop leg {leg.id} ({leg.player_name} - {leg.bet_type}/{leg.stat_type})")
            continue

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
                if existing_player.current_team:
                    leg.player_team = existing_player.current_team
                app.logger.info(f"[PLAYER-POPULATION] Found existing player {existing_player.player_name} (ID: {existing_player.id}) for leg {leg.id}")
                continue
            
            # Check if we've already created this player in this transaction
            new_player_in_session = None
            normalized_name = leg.player_name.lower().strip()
            for obj in db.session.new:
                if isinstance(obj, Player) and obj.normalized_name == normalized_name:
                    new_player_in_session = obj
                    break
            
            if new_player_in_session:
                # Reuse the player we just created in this transaction
                leg.player_id = new_player_in_session.id
                leg.player_position = new_player_in_session.position
                if new_player_in_session.current_team:
                    leg.player_team = new_player_in_session.current_team
                app.logger.info(f"[PLAYER-POPULATION] Reusing newly created player {new_player_in_session.player_name} (ID: {new_player_in_session.id}) for leg {leg.id}")
                continue
            
            # Player not found, search ESPN with enhanced fallback strategies
            # Determine sport and league from bet leg
            sport_param = "football" if leg.parlay_sport in ['NFL', None] else "basketball"
            league_param = leg.parlay_sport.lower() if leg.parlay_sport else "nfl"
            
            app.logger.info(f"[PLAYER-POPULATION] Player {leg.player_name} not found locally, searching ESPN with enhanced strategies (sport={sport_param}, league={league_param})...")
            espn_player_data = enhanced_player_search(leg.player_name, sport=sport_param, league=league_param)
            
            if espn_player_data:
                # Create new player record
                # Convert empty strings to None for integer fields
                jersey_number = espn_player_data['jersey_number']
                if jersey_number == '' or jersey_number is None:
                    jersey_number = None
                else:
                    try:
                        jersey_number = int(jersey_number)
                    except (ValueError, TypeError):
                        jersey_number = None
                
                new_player = Player(
                    player_name=espn_player_data['player_name'],
                    normalized_name=espn_player_data['player_name'].lower().strip(),
                    display_name=espn_player_data['player_name'],
                    sport=espn_player_data['sport'],
                    position=espn_player_data['position'],
                    jersey_number=jersey_number,
                    current_team=espn_player_data['current_team'],
                    team_abbreviation=espn_player_data['team_abbreviation'],
                    espn_player_id=espn_player_data['espn_player_id']
                )
                
                db.session.add(new_player)
                db.session.flush()  # Get the ID
                
                # Update the bet leg
                leg.player_id = new_player.id
                leg.player_position = new_player.position
                if new_player.current_team:
                    leg.player_team = new_player.current_team
                
                # CRITICAL FIX: Update leg sport if it differs (e.g. NFL -> NBA)
                # This allows populate_game_ids_for_bet to find the correct game
                if new_player.sport and leg.sport != new_player.sport:
                    app.logger.info(f"[PLAYER-POPULATION] Correcting sport for leg {leg.id}: {leg.sport} -> {new_player.sport}")
                    leg.sport = new_player.sport
                    leg.parlay_sport = new_player.sport
                
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
        db.session.rollback()

def save_bet_to_db(user_id: int, bet_data: dict, skip_duplicate_check: bool = False) -> dict:
    """Save a bet to database with JSON backup and create BetLeg records"""
    from models import Team, Bet, BetLeg

    # --- DUPLICATE CHECK LOGIC ---
    legs = bet_data.get('legs', [])
    if not skip_duplicate_check:
        core_fields = ['wager', 'potential_winnings', 'final_odds', 'bet_date']
        core_match = {f: bet_data.get(f) for f in core_fields}

        # Query all bets for user - limit to recent bets to avoid timeout
        user_bets = Bet.query.filter_by(user_id=user_id).order_by(Bet.created_at.desc()).limit(100).all()
        for existing_bet in user_bets:
            existing_data = existing_bet.get_bet_data()
            # Check for duplicate bets - use .get() to safely handle missing keys
            if existing_data.get('wager') == core_match['wager'] and existing_data.get('final_odds') == core_match['final_odds']:
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
    bet.betting_site_id = bet_data.get('bet_id') or bet_data.get('betting_site_id')
    bet.betting_site = bet_data.get('betting_site')  # FIX: Set betting_site from OCR data
    bet.bet_type = bet_data.get('bet_type', 'parlay')  # FIX: Set bet_type from OCR data
    bet.secondary_bettors = bet_data.get('secondary_bettor_ids', [])
    bet.is_active = True
    bet.is_archived = False
    bet.status = 'pending'
    bet.api_fetched = 'No'
    bet.created_at = datetime.now()  # FIX: Explicitly set created_at
    
    # Set the individual database columns
    bet.wager = bet_data.get('wager')
    bet.potential_winnings = bet_data.get('potential_winnings')
    bet.final_odds = bet_data.get('final_odds')
    
    # Handle bet_date - convert string to date object if needed
    bet_date_value = bet_data.get('bet_date')
    if bet_date_value:
        if isinstance(bet_date_value, str):
            try:
                bet.bet_date = datetime.strptime(bet_date_value, '%Y-%m-%d').date()
            except ValueError:
                # If parsing fails, use today's date
                bet.bet_date = datetime.now().date()
        else:
            bet.bet_date = bet_date_value
    else:
        bet.bet_date = datetime.now().date()
    
    db.session.add(bet)
    db.session.flush()
    
    # Capture bet ID after flush for return value
    bet_id = bet.id

    for leg_data in legs:
            game_date = None
            game_time = None
            if leg_data.get('game_date'):
                try:
                    import pytz
                    
                    game_date_str = str(leg_data['game_date']).strip()
                    app.logger.info(f"[GAME-DATE-DEBUG] leg_data['game_date'] = '{game_date_str}'")
                    
                    eastern_tz = pytz.timezone('US/Eastern')
                    
                    # Try parsing as ISO datetime with UTC timezone
                    try:
                        if 'T' in game_date_str:
                            # Full datetime string - parse as UTC and convert to Eastern
                            game_datetime_utc = datetime.fromisoformat(game_date_str.replace('Z', '+00:00'))
                            game_datetime_eastern = game_datetime_utc.astimezone(eastern_tz)
                            app.logger.info(f"[GAME-DATE-DEBUG] Parsed UTC datetime, converted: {game_datetime_eastern}")
                            game_date = game_datetime_eastern.date()
                            game_time = game_datetime_eastern.time()
                        else:
                            # Just a date string (YYYY-MM-DD) - treat as already Eastern time
                            game_date_obj = datetime.strptime(game_date_str, '%Y-%m-%d').date()
                            game_date = game_date_obj
                            app.logger.info(f"[GAME-DATE-DEBUG] Treated as Eastern date: {game_date}")
                            # continue  <-- REMOVED: This was skipping leg creation!
                    except ValueError as parse_error:
                        app.logger.error(f"[GAME-DATE-DEBUG] Parse error: {parse_error}. Treating as date only.")
                        # Last resort: try to parse as simple date (treat as Eastern)
                        game_date = datetime.strptime(game_date_str, '%Y-%m-%d').date()
                        
                except (ValueError, AttributeError, TypeError) as e:
                    app.logger.error(f"[GAME-DATE-DEBUG] Error parsing game_date: {e}")
                    pass
            
            # If game_date is still None, use today's date in Eastern timezone
            if game_date is None:
                import pytz
                eastern_tz = pytz.timezone('US/Eastern')
                game_date = datetime.now(eastern_tz).date()
                app.logger.info(f"[GAME-DATE-DEBUG] No game_date provided, using Eastern today: {game_date}")
            
            # SPORT VALIDATION & NORMALIZATION (FIX 1)
            VALID_SPORTS = {'NFL', 'NBA', 'MLB', 'NHL', 'NCAAF', 'NCAAB'}
            sport = leg_data.get('sport', 'NFL')
            if isinstance(sport, str):
                sport = sport.upper().strip()
            else:
                sport = 'NFL'
            
            if sport not in VALID_SPORTS:
                app.logger.warning(f"Invalid sport '{sport}' for leg '{leg_data.get('player_name')}'. Defaulting to NFL.")
                sport = 'NFL'
            
            team_value = leg_data.get('team_name')  # Use transformed field name
            if team_value:
                team_value = normalize_team_name(team_value, sport)
            
            # SANITIZATION: Handle "Game Total" or invalid team names from manual entry
            # This ensures populate_game_ids_for_bet falls back to player_team logic
            home_team = leg_data.get('home_team', '')
            if home_team and 'game total' in home_team.lower():
                home_team = ''
                
            away_team = leg_data.get('away_team', '')
            if away_team and 'game total' in away_team.lower():
                away_team = ''
                
            leg_status = leg_data.get('status', 'pending')
            bet_leg = BetLeg(
                bet_id=bet.id,
                player_name=leg_data.get('player_name') or team_value or 'Unknown',  # Use transformed field name
                player_team=team_value,
                home_team=home_team,
                away_team=away_team,
                game_date=game_date,
                game_time=game_time,
                sport=sport,
                bet_type=leg_data.get('bet_type', 'player_prop'),
                bet_line_type=leg_data.get('bet_line_type'),
                target_value=leg_data.get('target_value') or 0.0,  # Use transformed field name
                stat_type=leg_data.get('stat_type'),  # Use transformed field name
                status=leg_status,
                game_status='STATUS_SCHEDULED',  # Initialize with scheduled status
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
    
    # Commit the transaction with error handling
    try:
        db.session.commit()
        app.logger.info(f"Successfully committed bet {bet.id} with {len(legs)} legs")
        
        # Audit log the bet creation
        from helpers.audit_helpers import log_bet_created
        log_bet_created(db_session=db.session, bet_id=bet.id, user_id=user_id)
        db.session.commit()  # Commit audit log
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Database commit failed: {str(e)}")
        raise e
    
    # Backup to JSON with error handling
    try:
        backup_to_json(user_id)
    except Exception as e:
        app.logger.error(f"JSON backup failed: {str(e)}")
        # Don't raise - backup failure shouldn't break the bet save
    
    # Skip expensive operations for OCR bets to avoid timeouts
    if not skip_duplicate_check:
        # 1. Populate player data FIRST (so we can get team info from player)
        try:
            populate_player_data_for_bet(bet)
        except Exception as e:
            app.logger.error(f"[PLAYER-POPULATION] Error populating player data for bet {bet.id}: {e}")

        # 2. Populate ESPN game IDs (using team info from player if needed)
        try:
            populate_game_ids_for_bet(bet)
        except Exception as e:
            app.logger.error(f"[GAME-ID-POPULATION] Error populating game IDs for bet {bet.id}: {e}")
    
    # Skip expensive operations for OCR bets to avoid timeouts
    if not skip_duplicate_check:
        # ESPN API update trigger
        try:
            update_bet_legs_for_bet(bet)
        except Exception as e:
            app.logger.error(f"[ESPN-UPDATE] Error updating bet legs for bet {bet.id}: {e}")
    
    # Return bet data directly without triggering database queries
    return {
        'id': bet_id,
        'db_id': bet_id,
        'user_id': bet.user_id,
        'betting_site': bet.betting_site,
        'bet_type': bet.bet_type,
        'status': bet.status,
        'wager': bet.wager,
        'original_odds': bet.original_odds,
        'total_legs': bet.total_legs,
        'created_at': bet.created_at.isoformat() if bet.created_at and hasattr(bet.created_at, 'isoformat') else datetime.now().isoformat(),
        'bet_date': bet.bet_date,  # Already a string in the database
        'success': True,
        'message': 'Bet saved successfully'
    }
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
            # ONLY if game has been finalized (not unknown) AND achieved_value exists and isn't just the default 0
            if (bet_leg.status == 'pending' and bet_leg.is_hit is None and 
                bet_leg.achieved_value is not None and bet_leg.achieved_value != 0 and
                bet_leg.game_status != 'unknown' and bet_leg.game_status is not None):
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
                        elif status in ['STATUS_IN_PROGRESS', 'STATUS_HALFTIME']:
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
                    elif status in ['STATUS_IN_PROGRESS', 'STATUS_HALFTIME']:
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
    if not game_date_str or str(game_date_str).lower() == 'none':
        return False
    try:
        today = datetime.now().date()
        game_date = datetime.strptime(game_date_str, "%Y-%m-%d").date()
        return game_date < today
    except ValueError:
        return False

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


game_data_cache = {}




# Import automations from automation package (after app is set up to avoid circular imports)
from automation import (
    update_live_bet_legs,
    update_completed_bet_legs,
    standardize_bet_leg_team_names,
    auto_move_bets_no_live_legs,
    auto_determine_leg_hit_status,
    process_historical_bets_api
)

# Define wrapper functions for scheduler jobs
def run_update_completed_bet_legs():
    logger.info("[SCHEDULER] Running update_completed_bet_legs")
    with app.app_context():
        update_completed_bet_legs()

def run_update_live_bet_legs():
    logger.info("[SCHEDULER] Running update_live_bet_legs")
    with app.app_context():
        update_live_bet_legs()

def run_standardize_bet_leg_team_names():
    logger.info("[SCHEDULER] Running standardize_bet_leg_team_names")
    with app.app_context():
        standardize_bet_leg_team_names()

def run_auto_move_bets_no_live_legs():
    logger.info("[SCHEDULER] Running auto_move_bets_no_live_legs")
    with app.app_context():
        auto_move_bets_no_live_legs()

def run_auto_determine_leg_hit_status():
    logger.info("[SCHEDULER] Running auto_determine_leg_hit_status")
    with app.app_context():
        auto_determine_leg_hit_status()

def run_process_historical_bets_api():
    logger.info("[SCHEDULER] Running process_historical_bets_api")
    with app.app_context():
        from automation.historical_bet_processing import process_historical_bets_api
        process_historical_bets_api()

def run_populate_missing_game_ids():
    """Populate game IDs for bet legs that are missing them (e.g., OCR bets)"""
    logger.info("[SCHEDULER] Running populate_missing_game_ids")
    with app.app_context():
        try:
            # Find all bets with legs that have game_date but no game_id (None or empty string)
            # Also ensure we only pick up pending/live bets to avoid processing old completed ones unnecessarily
            bet_ids = db.session.query(Bet.id).join(
                BetLeg, BetLeg.bet_id == Bet.id
            ).filter(
                BetLeg.game_date.isnot(None),
                or_(BetLeg.game_id.is_(None), BetLeg.game_id == ''),
                BetLeg.status.in_(['pending', 'live'])
            ).distinct().all()
            
            if not bet_ids:
                # logger.info("[GAME-ID-POPULATION] No bets with missing game IDs found") # Reduce noise
                return
            
            logger.info(f"[GAME-ID-POPULATION] Found {len(bet_ids)} bets with missing game IDs: {[b[0] for b in bet_ids]}")
            
            for (bet_id,) in bet_ids:
                try:
                    bet = Bet.query.get(bet_id)
                    if bet:
                        populate_game_ids_for_bet(bet)
                except Exception as e:
                    logger.error(f"[GAME-ID-POPULATION] Error populating game IDs for bet {bet_id}: {e}")
        
        except Exception as e:
            logger.error(f"[GAME-ID-POPULATION] Error in run_populate_missing_game_ids: {e}")

def run_populate_missing_player_data():
    """Populate player data for bet legs that are missing it (e.g., OCR bets)"""
    logger.info("[SCHEDULER] Running populate_missing_player_data")
    with app.app_context():
        try:
            # Find all bets with legs that have missing player data
            # CRITICAL FIX: Do NOT filter by game_id.isnot(None). 
            # We need player data to be populated FIRST so we can correct the sport (e.g. NFL -> NBA)
            # and THEN find the game ID.
            bet_ids = db.session.query(Bet.id).join(
                BetLeg, BetLeg.bet_id == Bet.id
            ).filter(
                (BetLeg.achieved_value.is_(None) | (BetLeg.achieved_value == 0.0)),
                BetLeg.status == 'pending',
                # Only process legs that actually need player data (have a player name but no ID)
                BetLeg.player_name.isnot(None),
                BetLeg.player_name != 'Unknown',
                BetLeg.player_name != 'Game Total',
                BetLeg.player_id.is_(None)
            ).distinct().all()
            
            if not bet_ids:
                logger.info("[PLAYER-POPULATION] No bets with missing player data found")
                return
            
            logger.info(f"[PLAYER-POPULATION] Found {len(bet_ids)} bets with missing player data")
            
            for (bet_id,) in bet_ids:
                try:
                    bet = Bet.query.get(bet_id)
                    if bet:
                        populate_player_data_for_bet(bet)
                except Exception as e:
                    logger.error(f"[PLAYER-POPULATION] Error populating player data for bet {bet_id}: {e}")
        
        except Exception as e:
            logger.error(f"[PLAYER-POPULATION] Error in run_populate_missing_player_data: {e}")

def run_validate_historical_data():
    """Daily validation of historical bet data against ESPN API"""
    logger.info("[SCHEDULER] Running validate_historical_data")
    with app.app_context():
        try:
            from automation.data_validation import validate_historical_bet_data
            validate_historical_bet_data()
        except Exception as e:
            logger.error(f"[DATA-VALIDATION] Error in run_validate_historical_data: {e}")

def run_enrich_player_data():
    """Background job to enrich incomplete player data"""
    logger.info("[SCHEDULER] Running enrich_player_data")
    with app.app_context():
        try:
            from jobs.player_enrichment_job import enrich_player_data
            enrich_player_data()
        except Exception as e:
            logger.error(f"[PLAYER-ENRICHMENT] Error in run_enrich_player_data: {e}")

# Schedule automated tasks (moved outside if __name__ == '__main__' so it runs on Render)
scheduler.add_job(
    func=run_update_completed_bet_legs,
    trigger=IntervalTrigger(minutes=30),
    id='completed_bet_leg_updates',
    name='Update completed bet legs with final results every 30 minutes'
)

scheduler.add_job(
    func=run_update_live_bet_legs,
    trigger=IntervalTrigger(minutes=1),
    id='live_bet_updates',
    name='Update live bet legs with real-time data every minute'
)

scheduler.add_job(
    func=run_standardize_bet_leg_team_names,
    trigger=IntervalTrigger(hours=24),
    id='team_name_standardization',
    name='Standardize team names in bet_legs to use team_name_short daily'
)

scheduler.add_job(
    func=run_auto_move_bets_no_live_legs,
    trigger=IntervalTrigger(minutes=5),
    id='auto_move_no_live_legs',
    name='Move bets with no live legs to historical every 5 minutes'
)

scheduler.add_job(
    func=run_auto_determine_leg_hit_status,
    trigger=IntervalTrigger(minutes=10),
    id='auto_determine_hit_status',
    name='Determine hit/miss status for legs with achieved values every 10 minutes'
)

scheduler.add_job(
    func=run_process_historical_bets_api,
    trigger=IntervalTrigger(hours=1),
    id='historical_bet_processing',
    name='Process historical bets with ESPN API data and update status hourly'
)

scheduler.add_job(
    func=run_populate_missing_game_ids,
    trigger=IntervalTrigger(minutes=2),
    id='populate_missing_game_ids',
    name='Populate game IDs for bets with missing ESPN game links every 2 minutes'
)

scheduler.add_job(
    func=run_populate_missing_player_data,
    trigger=IntervalTrigger(minutes=3),
    id='populate_missing_player_data',
    name='Populate player data for bets with missing stats every 3 minutes'
)

scheduler.add_job(
    func=run_validate_historical_data,
    trigger=CronTrigger(hour=3, minute=0, timezone='US/Eastern'),
    id='validate_historical_data',
    name='Validate historical bet data against ESPN API daily at 3 AM ET'
)

scheduler.add_job(
    func=run_enrich_player_data,
    trigger=IntervalTrigger(minutes=5),
    id='enrich_player_data',
    name='Enrich incomplete player data every 5 minutes'
)

scheduler.add_job(
    func=lambda: app.app_context().push() or __import__('update_teams').update_teams(),
    trigger=CronTrigger(hour=4, minute=0, timezone='US/Eastern'),
    id='daily_team_update',
    name='Update team data from ESPN daily at 4 AM ET'
)

# Run diagnostics on startup
try:
    from automation.bet_status_management import log_bet_status_distribution
    scheduler.add_job(
        func=log_bet_status_distribution,
        trigger='date', # Run once immediately
        id='startup_diagnostics',
        name='Run bet status diagnostics on startup'
    )
except ImportError:
    pass

# Start the scheduler
scheduler.start()

if __name__ == '__main__':
    # Run migrations on startup (Local dev only)
    try:
        print("Running database migrations...")
        import subprocess
        import sys
        subprocess.run([sys.executable, '-m', 'flask', 'db', 'upgrade'], check=True)
        print("Database migrations completed successfully.")
    except Exception as e:
        print(f"Database migration failed: {e}")

    # Run debug script (Local dev only)
    try:
        from debug_scoreboard import debug_scoreboard
        print("Running startup debug...")
        debug_scoreboard()
    except Exception as e:
        print(f"Startup debug failed: {e}")

    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
