# app.py - Parlay Tracker Backend - Multi-User Edition
# Force redeploy: 2025-11-01 00:00
from flask import Flask, jsonify, send_from_directory, request, session, redirect, url_for
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import requests
import os
from datetime import datetime
import json
import atexit

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Import database models
from models import db, User, Bet, BetLeg, bet_users

# Data directory for JSON fixtures
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def data_path(filename):
    return os.path.join(DATA_DIR, filename)

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Log data directory contents on startup
try:
    data_files = os.listdir(DATA_DIR)
    print(f"[STARTUP] Data directory ({DATA_DIR}) contains: {data_files}")
    for fname in data_files:
        fpath = os.path.join(DATA_DIR, fname)
        if os.path.isfile(fpath):
            size = os.path.getsize(fpath)
            print(f"[STARTUP]   {fname}: {size} bytes")
except Exception as e:
    print(f"[STARTUP] Error listing data directory: {e}")


def _parse_american_odds(odds):
    """Parse American odds like +150 or -120 and return decimal multiplier (including stake).
    Returns None if odds cannot be parsed.
    """
    if odds is None:
        return None
    # allow numeric input as well
    try:
        # strip whitespace
        s = str(odds).strip()
        # if empty
        if s == "":
            return None
        # remove plus if present
        if s.startswith("+"):
            val = int(s[1:])
            return 1 + (val / 100.0)
        if s.startswith("-"):
            val = int(s[1:])
            if val == 0:
                return None
            return 1 + (100.0 / val)
        # try plain integer
        if s.isdigit() or (s[0] == '-' and s[1:].isdigit()):
            val = int(s)
            if val > 0:
                return 1 + (val / 100.0)
            else:
                return 1 + (100.0 / abs(val))
        # fallback: try float (decimal odds)
        f = float(s)
        if f > 0:
            return f
    except Exception:
        return None
    return None


def _compute_parlay_returns_from_odds(wager, parlay_odds=None, leg_odds_list=None):
    """Compute expected profit (returns) from wager and odds.
    If parlay_odds provided (American odds string), use that. Otherwise, if leg_odds_list
    provided, compute combined multiplier. Returns numeric profit or None if not computable.
    """
    try:
        if wager is None:
            return None
        w = float(wager)
        # prefer parlay odds
        if parlay_odds:
            mult = _parse_american_odds(parlay_odds)
            if mult is None:
                return None
            # profit is wager * (mult - 1)
            return round(w * (mult - 1), 2)

        # else try combined leg odds
        if leg_odds_list:
            mult = 1.0
            any_parsed = False
            for o in leg_odds_list:
                pm = _parse_american_odds(o)
                if pm is None:
                    continue
                any_parsed = True
                mult *= pm
            if any_parsed:
                return round(w * (mult - 1), 2)

        return None
    except Exception:
        return None


from functools import wraps

def get_user_bets_query(user, **filters):
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
                # Handle IN clause for lists
                query = query.filter(getattr(Bet, key).in_(value))
            else:
                query = query.filter(getattr(Bet, key) == value)
    
    return query

# Configure Flask to serve static files from root directory
app = Flask(__name__, static_folder='.', static_url_path='')

# Database configuration
# Get DATABASE_URL from environment, default to SQLite for local dev
database_url = os.environ.get('DATABASE_URL', 'sqlite:///parlays.db')

# Fix for Render PostgreSQL: Render uses postgres:// but SQLAlchemy needs postgresql://
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

# Add SSL mode for PostgreSQL connections
if database_url.startswith('postgresql://'):
    if '?' in database_url:
        database_url += '&sslmode=require'
    else:
        database_url += '?sslmode=require'

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize extensions
CORS(app, supports_credentials=True)
db.init_app(app)

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Setup background scheduler for automated tasks
scheduler = BackgroundScheduler()
scheduler.start()

# Shut down scheduler on app exit
atexit.register(lambda: scheduler.shutdown())

# Helper function to use database with JSON backup
def get_user_bets_from_db(user_id, status_filter=None):
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

def save_bet_to_db(user_id, bet_data):
    """Save a bet to database with JSON backup"""
    try:
        bet = Bet(user_id=user_id)
        bet.set_bet_data(bet_data)
        db.session.add(bet)
        db.session.commit()
        
        # Also backup to JSON
        backup_to_json(user_id)
        
        return bet.to_dict()
    except Exception as e:
        app.logger.error(f"Error saving bet to database: {e}")
        db.session.rollback()
        raise

def has_complete_final_data(bet_data):
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


def save_final_results_to_bet(bet, processed_data):
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
        bet_legs = bet.bet_legs_rel.order_by(BetLeg.leg_order).all()
        
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
                            updated = True
                            app.logger.info(f"Set status={leg_status} for leg {i}: {bet_leg.player_name or bet_leg.team}")
        
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
    
    This runs periodically (every 5 minutes) to ensure completed bets get their final results.
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
            bet_legs = bet.bet_legs_rel.order_by(BetLeg.leg_order).all()
            
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
                    if bet_leg.status == 'pending' and bet_leg.achieved_value is not None:
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
                        leg_updated = True
                        app.logger.info(f"[AUTO-UPDATE] Bet {bet.id} Leg {i+1}: status = {leg_status}")
                    
                    if leg_updated:
                        updated_legs += 1
                
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
            if leg.status == 'pending' or leg.is_hit is None:
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
                        
                        # Update is_hit (True for won, False for lost)
                        is_hit_value = True if leg_status == 'won' else False
                        if leg.is_hit != is_hit_value:
                            leg.is_hit = is_hit_value
                            leg_updated = True
        
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
                        returns = _compute_parlay_returns_from_odds(parlay_wager, parlay_odds, leg_odds)
                        if returns is not None:
                            returns = f"{returns:.2f}"
                    parlay['returns'] = returns
                    historical_parlays.append(parlay)
            elif any_game_active:
                if parlay_id not in existing_live:
                    returns = parlay.get('returns')
                    if returns is None or (isinstance(returns, str) and str(returns).strip() == ""):
                        returns = _compute_parlay_returns_from_odds(parlay_wager, parlay_odds, leg_odds)
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
                    returns = _compute_parlay_returns_from_odds(parlay_wager, parlay_odds, leg_odds)
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
                    returns = _compute_parlay_returns_from_odds(parlay_wager, parlay_odds, leg_odds)
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
    stat = bet["stat"].strip().lower()  # Normalize to lowercase for comparisons
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
                        bet_team_norm = bet_team.lower().strip()
                        home_team_norm = home_team.lower().strip()
                        away_team_norm = away_team.lower().strip()
                        
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


def compute_and_persist_returns(force=False):
    """Compute missing returns for all Data files and persist them.
    If force=True, overwrite existing returns when computable.
    Returns a dict of {filename: [(parlay_name, returns), ...]}"""
    results = {}
    for fname in ("Historical_Bets.json", "Live_Bets.json", "Todays_Bets.json"):
        path = data_path(fname)
        try:
            with open(path) as f:
                data = json.load(f)
        except Exception:
            data = []

        updated = []
        for parlay in data:
            parlay_odds = parlay.get('odds')
            parlay_wager = parlay.get('wager')
            leg_odds = [l.get('odds') for l in parlay.get('legs', []) if l.get('odds') is not None]
            current = parlay.get('returns')
            if force or current is None or (isinstance(current, str) and str(current).strip() == ""):
                val = _compute_parlay_returns_from_odds(parlay_wager, parlay_odds, leg_odds)
                if val is not None:
                    # ensure 2 decimal places and format as string
                    val = round(float(val), 2)
                    parlay['returns'] = f"{val:.2f}"
                    updated.append((parlay.get('name'), val))

        # write back
        try:
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            app.logger.error(f"Failed to persist {path}: {e}")

        results[fname] = updated

    return results


# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.route('/auth/register', methods=['POST'])
@login_required
def register():
    """Register a new user (admin only)"""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # For invite-only: you can add admin check here
    # if current_user.email != 'admin@example.com':
    #     return jsonify({'error': 'Admin only'}), 403
    
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if user already exists (case-insensitive)
    if User.query.filter(db.func.lower(User.username) == username.lower()).first():
        return jsonify({'error': 'Username already exists'}), 400
    if User.query.filter(db.func.lower(User.email) == email.lower()).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    try:
        # Store username with original capitalization (but check uniqueness case-insensitively)
        user = User(username=username, email=email.lower())
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return jsonify({
            'message': 'User created successfully',
            'user': user.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Registration error: {e}")
        return jsonify({'error': 'Failed to create user'}), 500


@app.route('/auth/login', methods=['POST'])
def login():
    """Login with username/email and password (case-insensitive)"""
    data = request.json
    identifier = data.get('username') or data.get('email')
    password = data.get('password')
    
    if not identifier or not password:
        return jsonify({'error': 'Missing credentials'}), 400
    
    # Try to find user by username or email (case-insensitive)
    user = User.query.filter(
        (db.func.lower(User.username) == identifier.lower()) | 
        (db.func.lower(User.email) == identifier.lower())
    ).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Account is disabled'}), 403
    
    login_user(user)
    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict()
    }), 200


@app.route('/auth/logout', methods=['POST'])
@login_required
def logout():
    """Logout current user"""
    logout_user()
    return jsonify({'message': 'Logout successful'}), 200


@app.route('/auth/check', methods=['GET'])
def check_auth():
    """Check if user is authenticated"""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user': current_user.to_dict()
        }), 200
    return jsonify({'authenticated': False}), 200


# ============================================================================
# Page Routes
# ============================================================================

@app.route("/live")
@login_required
def live():
    # Get live bets using many-to-many relationship
    bets = get_user_bets_query(
        current_user,
        is_active=True,
        is_archived=False,
        status='live'
    ).all()
    # Convert Bet objects to dict format - use_live_data=True forces ESPN API fetch for real-time stats
    live_parlays = [bet.to_dict_structured(use_live_data=True) for bet in bets]
    processed = process_parlay_data(live_parlays)
    return jsonify(sort_parlays_by_date(processed))



@app.route("/todays")
@login_required
def todays():
    # Auto-move completed bets (games that have ended)
    auto_move_completed_bets(current_user.id)
    
    # Get today's bets using many-to-many relationship
    bets = get_user_bets_query(
        current_user,
        is_active=True,
        is_archived=False,
        status='pending'
    ).all()
    # Use live data for today's bets too (games might have started)
    todays_parlays = [bet.to_dict_structured(use_live_data=True) for bet in bets]
    # Return the raw today's bets
    processed = process_parlay_data(todays_parlays)
    return jsonify(sort_parlays_by_date(processed))

@app.route("/historical")
@login_required
def historical():
    try:
        app.logger.info("Starting historical endpoint processing")
        
        # Load historical parlays using many-to-many relationship
        try:
            bets = get_user_bets_query(
                current_user,
                is_active=False,
                is_archived=False
            ).all()
            # Use use_live_data=False to check if we have saved data first
            # If data exists (achieved_value, game_status), use it; otherwise fetch from ESPN
            historical_parlays = [bet.to_dict_structured(use_live_data=False) for bet in bets]  # Use structured DB with jersey numbers
            app.logger.info(f"Loaded {len(historical_parlays)} historical parlays")
            for parlay in historical_parlays:
                app.logger.info(f"Parlay: {parlay.get('name')}, type: {parlay.get('type')}, legs: {len(parlay.get('legs', []))}")
        except Exception as e:
            app.logger.error(f"Error loading historical bets: {str(e)}")
            raise
            
        if not historical_parlays:
            app.logger.warning("No historical parlays found")
            return jsonify([])
        
        # For historical bets, separate into three categories:
        # 1. Bets with complete final data (no fetch needed)
        # 2. Bets marked api_fetched='No' (still need live updates - e.g., lost bet with unfinished games)
        # 3. Newly added old bets without data (fetch once to get historical data)
        
        bets_with_results = []  # Complete data - no fetch needed
        bets_needing_live_fetch = []  # api_fetched='No' - continue fetching
        bets_needing_initial_fetch = []  # New old bets - fetch once
        
        # Get the actual Bet objects
        bet_objects = {bet.id: bet for bet in bets}
        
        for parlay in historical_parlays:
            bet_obj = bet_objects.get(parlay.get('db_id'))
            
            # Check if bet explicitly needs continued fetching (lost bet with games still in progress)
            if bet_obj and bet_obj.api_fetched == 'No':
                app.logger.info(f"Bet {parlay.get('name')} marked for continued ESPN fetch (lost bet with games in progress)")
                bets_needing_live_fetch.append(parlay)
                continue
            
            # Check if legs have final results stored
            if has_complete_final_data(parlay):
                bets_with_results.append(parlay)
            else:
                # Newly added old bet or bet without data yet
                bets_needing_initial_fetch.append(parlay)
        
        app.logger.info(f"Historical bets: {len(bets_with_results)} complete, "
                       f"{len(bets_needing_live_fetch)} need live updates, "
                       f"{len(bets_needing_initial_fetch)} need initial fetch")
        
        # Fetch ESPN data for bets that need it
        # This includes:
        # 1. Bets with api_fetched='No' (lost bets with games still in progress - need live updates)
        # 2. Newly added old bets without data (fetch once to get historical data)
        processed = []
        bets_to_fetch = bets_needing_live_fetch + bets_needing_initial_fetch
        
        if bets_to_fetch:
            app.logger.info(f"Fetching ESPN data for {len(bets_to_fetch)} historical bets")
            
            for parlay in bets_to_fetch:
                bet_obj = bet_objects.get(parlay.get('db_id'))
                is_live_fetch = bet_obj and bet_obj.api_fetched == 'No'
                
                if is_live_fetch:
                    app.logger.info(f"Live fetch for {parlay.get('name')} (lost bet with games in progress)")
                else:
                    app.logger.info(f"Initial fetch for {parlay.get('name')} (newly added old bet)")
            
            try:
                processed = process_parlay_data(bets_to_fetch)
                
                # Process each fetched bet
                for parlay in processed:
                    bet_obj = bet_objects.get(parlay.get('db_id'))
                    if bet_obj:
                        is_live_fetch = bet_obj.api_fetched == 'No'
                        
                        if is_live_fetch:
                            # For lost bets with games still in progress, check if all games are now finished
                            all_finished = True
                            for game in parlay.get('games', []):
                                if game.get('statusTypeName') != 'STATUS_FINAL':
                                    all_finished = False
                                    break
                            
                            if all_finished:
                                # All games finished - save final results and mark as complete
                                save_final_results_to_bet(bet_obj, [parlay])
                                bet_obj.api_fetched = 'Yes'
                                bet_obj.status = 'completed'
                                app.logger.info(f"✅ All games finished for {parlay.get('name')} - saved final results")
                            else:
                                # Games still in progress - keep fetching
                                app.logger.info(f"⏳ Games still in progress for {parlay.get('name')} - will continue fetching")
                        else:
                            # Initial fetch for newly added old bet - save results
                            save_final_results_to_bet(bet_obj, [parlay])
                            bet_obj.api_fetched = 'Yes'
                            app.logger.info(f"✅ Saved initial data for {parlay.get('name')}")
                
                db.session.commit()
                app.logger.info(f"✅ Processed {len(processed)} historical bets")
                
            except Exception as e:
                app.logger.error(f"Error processing historical bets: {str(e)}")
                # If processing fails, use unprocessed data
                processed = bets_to_fetch
                # Add empty games array for frontend compatibility
                for parlay in processed:
                    if 'games' not in parlay:
                        parlay['games'] = []
        
        # For bets with results, just add empty games array (display uses stored data)
        processed_with_results = []
        for parlay in bets_with_results:
            # Add empty games array (no live ESPN data needed for completed bets)
            if 'games' not in parlay:
                parlay['games'] = []
            processed_with_results.append(parlay)
        
        # Combine all historical bets
        all_historical = processed_with_results + processed
        app.logger.info(f"Total historical bets to return: {len(all_historical)}")
        
        # Sort and return
        try:
            sorted_parlays = sort_parlays_by_date(all_historical)
            app.logger.info(f"Returning {len(sorted_parlays)} sorted historical parlays")
            return jsonify(sorted_parlays)
        except Exception as e:
            app.logger.error(f"Error sorting parlays: {str(e)}")
            raise
            
    except Exception as e:
        app.logger.error(f"Error in historical endpoint: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route("/stats")
@login_required
def stats():
    # Auto-move completed bets (games that have ended)
    auto_move_completed_bets(current_user.id)
    
    # Clear game data cache to force fresh ESPN API calls
    global game_data_cache
    game_data_cache = {}
    
    # Get pending bets to process
    pending_bets = get_user_bets_from_db(current_user.id, status_filter='pending')
    parlays = [bet.get_bet_data() for bet in pending_bets]
    processed_parlays = process_parlay_data(parlays)
    
    # DON'T process/move parlays on every stats request - that clears Live_Bets.json!
    # process_parlays(processed_parlays)
    
    # Return processed live parlays for display
    live_bets = get_user_bets_from_db(current_user.id, status_filter='live')
    live_parlays = [bet.get_bet_data() for bet in live_bets]
    processed_live = process_parlay_data(live_parlays)
    return jsonify(sort_parlays_by_date(processed_live))

@app.route('/admin/compute_returns', methods=['POST'])
@login_required
def admin_compute_returns():
    """Admin endpoint to compute (and optionally force) returns.
    POST JSON body: {"force": true|false}
    Returns a JSON summary of updates.
    """
    try:
        body = request.get_json() or {}
        force = bool(body.get('force', False))
        results = compute_and_persist_returns(force=force)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin/update_teams', methods=['POST'])
@login_required
def admin_update_teams():
    """Admin endpoint to manually trigger team data update.
    Forces update regardless of last update time.
    """
    try:
        import subprocess
        
        # Run the update script
        result = subprocess.run(
            ['python', 'update_team_records.py'],
            cwd=os.path.dirname(__file__),
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': 'Team data updated successfully',
                'output': result.stdout
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Update script failed',
                'output': result.stderr
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Update timed out after 2 minutes'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/admin/move_completed', methods=['POST'])
@login_required
def admin_move_completed():
    """Admin endpoint to move completed games from pending/live to completed status.
    Checks ESPN API to see which games are STATUS_FINAL and updates their status.
    Returns a JSON summary of what was moved.
    """
    try:
        # Get pending and live bets for current user
        pending_bets = get_user_bets_from_db(current_user.id, status_filter='pending')
        live_bets = get_user_bets_from_db(current_user.id, status_filter='live')
        
        moved_parlays = []
        remaining_pending = 0
        remaining_live = 0
        
        # Check each pending bet
        for bet in pending_bets:
            parlay = bet.get_bet_data()
            if not parlay.get('legs'):
                remaining_pending += 1
                continue
            
            # Check if all games are complete
            all_games_complete = True
            for leg in parlay['legs']:
                game_date = leg.get('game_date')
                if not game_date:
                    all_games_complete = False
                    break
                
                events = get_events(game_date)
                found_game = False
                for event in events:
                    team_names = {c['team']['displayName'] for c in event['competitions'][0]['competitors']}
                    if leg['away'] in team_names and leg['home'] in team_names:
                        found_game = True
                        status = event['status']['type']['name']
                        if status != 'STATUS_FINAL':
                            all_games_complete = False
                            break
                        break
                
                if not found_game:
                    app.logger.warning(f"[Pending] Game not found: {leg['away']} @ {leg['home']} on {game_date}")
                    all_games_complete = False
                    break
                
                if not all_games_complete:
                    break
            
            # Update status to completed if all games are final
            if all_games_complete:
                bet.status = 'completed'
                db.session.commit()
                moved_parlays.append(parlay['name'])
                app.logger.info(f"Moving pending bet to completed: {parlay['name']}")
            else:
                remaining_pending += 1
        
        # Check each live bet
        for bet in live_bets:
            parlay = bet.get_bet_data()
            if not parlay.get('legs'):
                remaining_live += 1
                continue
            
            # Check if all games are complete
            all_games_complete = True
            for leg in parlay['legs']:
                game_date = leg.get('game_date')
                if not game_date:
                    all_games_complete = False
                    break
                
                events = get_events(game_date)
                found_game = False
                for event in events:
                    team_names = {c['team']['displayName'] for c in event['competitions'][0]['competitors']}
                    if leg['away'] in team_names and leg['home'] in team_names:
                        found_game = True
                        status = event['status']['type']['name']
                        if status != 'STATUS_FINAL':
                            all_games_complete = False
                            break
                        break
                
                if not found_game:
                    app.logger.warning(f"[Live] Game not found: {leg['away']} @ {leg['home']} on {game_date}")
                    all_games_complete = False
                    break
                
                if not all_games_complete:
                    break
            
            # Update status to completed if all games are final
            if all_games_complete:
                bet.status = 'completed'
                db.session.commit()
                moved_parlays.append(parlay['name'])
                app.logger.info(f"Moving live bet to completed: {parlay['name']}")
            else:
                remaining_live += 1
        
        # Backup to JSON after changes
        backup_to_json(current_user.id)
        
        total_remaining = remaining_pending + remaining_live
        
        return jsonify({
            "moved": moved_parlays,
            "moved_count": len(moved_parlays),
            "remaining_live": total_remaining,
            "remaining_pending": remaining_pending,
            "remaining_live_only": remaining_live
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in admin_move_completed: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/admin/export_files', methods=['GET'])
@login_required
def admin_export_files():
    """Admin endpoint to export all user bets as JSON.
    Returns all three categories (Live, Pending, Historical) in one response.
    Use this to sync remote state back to local.
    """
    try:
        pending_bets = get_user_bets_from_db(current_user.id, status_filter='pending')
        live_bets = get_user_bets_from_db(current_user.id, status_filter='live')
        historical_bets = get_user_bets_from_db(current_user.id, status_filter='completed')
        
        return jsonify({
            "live_bets": [bet.get_bet_data() for bet in live_bets],
            "todays_bets": [bet.get_bet_data() for bet in pending_bets],
            "historical_bets": [bet.get_bet_data() for bet in historical_bets]
        })
    except Exception as e:
        app.logger.error(f"Error in admin_export_files: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/bets', methods=['POST'])
@login_required
def create_bet():
    """Create a new bet for the current user"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Save bet to database with backup
        bet_id = save_bet_to_db(current_user.id, data)
        
        return jsonify({
            'message': 'Bet created successfully',
            'bet_id': bet_id
        }), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating bet: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/bets/<int:bet_id>', methods=['PUT'])
@login_required
def update_bet(bet_id):
    """Update an existing bet"""
    try:
        # Check if user has access to this bet
        bet = get_user_bets_query(current_user).filter(Bet.id == bet_id).first()
        if not bet:
            return jsonify({'error': 'Bet not found'}), 404
        
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update bet data
        bet.set_bet_data(data)
        
        # Update other fields if provided
        if 'status' in data:
            old_status = bet.status
            bet.status = data['status']
            # If marking as completed/won/lost, update is_active and api_fetched
            if data['status'] in ['completed', 'won', 'lost']:
                bet.is_active = False
                
                # Try to fetch and save final results if transitioning to completed
                # and bet doesn't already have complete final data
                if old_status not in ['completed', 'won', 'lost'] and not has_complete_final_data(data):
                    app.logger.info(f"Bet {bet.id} manually marked complete - attempting to fetch final results")
                    try:
                        processed_data = process_parlay_data([data])
                        save_final_results_to_bet(bet, processed_data)
                        app.logger.info(f"✅ Saved final results for manually completed bet {bet.id}")
                    except Exception as e:
                        app.logger.error(f"Failed to fetch final results for bet {bet.id}: {e}")
                
                bet.api_fetched = 'Yes'  # Mark as fetched
        if 'bet_type' in data:
            bet.bet_type = data['bet_type']
        if 'betting_site' in data:
            bet.betting_site = data['betting_site']
        
        db.session.commit()
        backup_to_json(current_user.id)
        
        return jsonify({
            'message': 'Bet updated successfully',
            'bet': bet.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating bet: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/bets/<int:bet_id>', methods=['DELETE'])
@login_required
def delete_bet(bet_id):
    """Delete a bet"""
    try:
        # Check if user has access to this bet
        bet = get_user_bets_query(current_user).filter(Bet.id == bet_id).first()
        if not bet:
            return jsonify({'error': 'Bet not found'}), 404
        
        db.session.delete(bet)
        db.session.commit()
        backup_to_json(current_user.id)
        
        return jsonify({'message': 'Bet deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting bet: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/bets/<int:bet_id>/archive', methods=['PUT'])
@login_required
def archive_bet(bet_id):
    """Archive a bet - changes status to 'archived'"""
    try:
        # Check if user has access to this bet
        bet = get_user_bets_query(current_user).filter(Bet.id == bet_id).first()
        if not bet:
            return jsonify({'error': 'Bet not found'}), 404
        
        # Update status to archived
        bet.status = 'archived'
        bet.updated_at = datetime.utcnow()
        
        # Also update the status in the bet_data JSON
        bet_data = bet.get_bet_data()
        bet_data['status'] = 'archived'
        bet.set_bet_data(bet_data, preserve_status=True)
        
        db.session.commit()
        backup_to_json(current_user.id)
        
        return jsonify({
            'message': 'Bet archived successfully',
            'bet': bet.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error archiving bet: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/archived', methods=['GET'])
@login_required
def get_archived_bets():
    """Get all archived bets for the current user (is_archived=1)"""
    try:
        archived_bets = get_user_bets_query(
            current_user,
            is_archived=True
        ).order_by(Bet.bet_date.desc()).all()
        
        bets_data = [bet.to_dict_structured() for bet in archived_bets]
        
        return jsonify({
            'archived': bets_data,
            'count': len(bets_data)
        }), 200
    except Exception as e:
        app.logger.error(f"Error fetching archived bets: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/bets/bulk-archive', methods=['POST'])
@login_required
def bulk_archive_bets():
    """Archive multiple bets at once"""
    try:
        data = request.get_json()
        bet_ids = data.get('bet_ids', [])
        
        if not bet_ids or not isinstance(bet_ids, list):
            return jsonify({'error': 'bet_ids must be a non-empty array'}), 400
        
        # Update all specified bets to archived
        updated_count = Bet.query.filter(
            Bet.id.in_(bet_ids),
            Bet.user_id == current_user.id  # Security: only user's own bets
        ).update(
            {
                'is_archived': True,
                'updated_at': datetime.utcnow()
            },
            synchronize_session=False
        )
        
        db.session.commit()
        backup_to_json(current_user.id)
        
        return jsonify({
            'success': True,
            'archived_count': updated_count,
            'message': f'Successfully archived {updated_count} bet(s)'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error bulk archiving bets: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/bets/bulk-unarchive', methods=['POST'])
@login_required
def bulk_unarchive_bets():
    """Unarchive multiple bets at once - returns them to Historical"""
    try:
        data = request.get_json()
        bet_ids = data.get('bet_ids', [])
        
        if not bet_ids or not isinstance(bet_ids, list):
            return jsonify({'error': 'bet_ids must be a non-empty array'}), 400
        
        # Update all specified bets to unarchived (back to historical)
        updated_count = Bet.query.filter(
            Bet.id.in_(bet_ids),
            Bet.user_id == current_user.id  # Security: only user's own bets
        ).update(
            {
                'is_archived': False,
                'is_active': False,  # Return to historical (not live)
                'updated_at': datetime.utcnow()
            },
            synchronize_session=False
        )
        
        db.session.commit()
        backup_to_json(current_user.id)
        
        return jsonify({
            'success': True,
            'unarchived_count': updated_count,
            'message': f'Successfully unarchived {updated_count} bet(s)'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error bulk unarchiving bets: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ========================================
# BET SLIP OCR API (GPT-4 Vision)
# ========================================

@app.route('/api/upload-betslip', methods=['POST'])
@login_required
def upload_betslip():
    """Extract bet information from uploaded bet slip image using GPT-4 Vision"""
    import base64
    from openai import OpenAI
    
    # Check if API key is configured
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key or openai_key == 'your-openai-api-key-here':
        return jsonify({
            'error': 'OpenAI API key not configured',
            'message': 'Please add your OPENAI_API_KEY to the .env file'
        }), 500
    
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    image_file = request.files['image']
    
    if image_file.filename == '':
        return jsonify({'error': 'No image selected'}), 400
    
    try:
        # Read and encode image
        image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Determine image type
        file_ext = image_file.filename.lower().split('.')[-1]
        mime_type = f"image/{file_ext if file_ext in ['png', 'jpeg', 'jpg', 'gif', 'webp'] else 'jpeg'}"
        
        # Create OpenAI client
        client = OpenAI(api_key=openai_key)
        
        # Create detailed prompt for GPT-4 Vision
        prompt = """
Analyze this bet slip image and extract ALL information in JSON format.

Extract:
- bet_site: Name of betting platform (DraftKings, FanDuel, BetMGM, Caesars, etc.)
- bet_type: "parlay" or "single"
- total_odds: American odds format (e.g., +450, -110)
- wager_amount: Dollar amount wagered (number only, no $ symbol)
- potential_payout: Potential total payout/winnings (number only)
- bet_date: Date of bet in YYYY-MM-DD format (if visible, otherwise today's date)
- legs: Array of individual bets, each containing:
  - sport: NFL, NBA, MLB, NHL, NCAAF, NCAAB, etc.
  - player_name: Full player name (for player props) or null
  - team_name: Full team name or abbreviation
  - home_team: Home team name/abbreviation
  - away_team: Away team name/abbreviation
  - bet_type: "player_prop", "moneyline", "spread", "total", "team_total"
  - stat_type: For props (e.g., "Passing Yards", "Receiving Yards", "Points", "Rebounds")
  - bet_line_type: "over" or "under" (for props/totals), null for spreads/moneyline
  - target_value: The line (e.g., 250.5 for yards, 6.5 for spread, 45.5 for totals)
  - odds: Individual leg odds in American format (e.g., -110, +150)
  - game_info: "Away Team @ Home Team" format
  - game_date: Date/time of game if visible (YYYY-MM-DD HH:MM format)

IMPORTANT RULES:
1. For player props: Include player_name, stat_type (yards/points/etc), bet_line_type (over/under), target_value
2. For spreads: Use bet_type="spread", target_value=spread amount (positive for underdog, negative for favorite)
3. For moneyline: Use bet_type="moneyline", team_name=team you're betting on
4. For totals: Use bet_type="total", bet_line_type="over" or "under", target_value=total points line
5. All odds should be in American format with + or - prefix
6. wager_amount and potential_payout should be numbers without $ symbols
7. If a field is not visible or unclear, use null

Return ONLY valid JSON. No additional text or explanation.

Example output format:
{
  "bet_site": "DraftKings",
  "bet_type": "parlay",
  "total_odds": "+450",
  "wager_amount": 25.00,
  "potential_payout": 137.50,
  "bet_date": "2024-11-12",
  "legs": [
    {
      "sport": "NFL",
      "player_name": "Justin Jefferson",
      "team_name": "Vikings",
      "home_team": "Bears",
      "away_team": "Vikings",
      "bet_type": "player_prop",
      "stat_type": "Receiving Yards",
      "bet_line_type": "over",
      "target_value": 75.5,
      "odds": "-110",
      "game_info": "Vikings @ Bears",
      "game_date": "2024-11-12 13:00"
    },
    {
      "sport": "NFL",
      "player_name": null,
      "team_name": "Lions",
      "home_team": "Packers",
      "away_team": "Lions",
      "bet_type": "spread",
      "stat_type": null,
      "bet_line_type": null,
      "target_value": -3.5,
      "odds": "-110",
      "game_info": "Lions @ Packers",
      "game_date": "2024-11-12 16:00"
    }
  ]
}
"""
        
        app.logger.info(f"[OCR] Processing bet slip for user {current_user.username}")
        
        # Call GPT-4 Vision API
        response = client.chat.completions.create(
            model="gpt-4o",  # Latest GPT-4 with vision
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_data}",
                                "detail": "high"  # High detail for better text extraction
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000,
            temperature=0.1  # Low temperature for consistent extraction
        )
        
        # Parse response
        extracted_text = response.choices[0].message.content
        app.logger.info(f"[OCR] GPT-4 response: {extracted_text[:200]}...")
        
        # Extract JSON from response (sometimes GPT adds markdown code blocks)
        if '```json' in extracted_text:
            extracted_text = extracted_text.split('```json')[1].split('```')[0].strip()
        elif '```' in extracted_text:
            extracted_text = extracted_text.split('```')[1].split('```')[0].strip()
        
        bet_data = json.loads(extracted_text)
        
        app.logger.info(f"[OCR] Successfully extracted bet data: {len(bet_data.get('legs', []))} legs")
        
        return jsonify({
            'success': True,
            'data': bet_data,
            'message': 'Bet slip processed successfully. Please review and confirm.'
        })
        
    except json.JSONDecodeError as e:
        app.logger.error(f"[OCR] Failed to parse JSON: {e}")
        app.logger.error(f"[OCR] Response text: {extracted_text if 'extracted_text' in locals() else 'N/A'}")
        return jsonify({
            'error': 'Failed to parse bet data from image',
            'details': str(e),
            'raw_response': extracted_text if 'extracted_text' in locals() else None
        }), 500
    except Exception as e:
        app.logger.error(f"[OCR] Bet slip extraction error: {e}")
        return jsonify({
            'error': 'Failed to process bet slip',
            'details': str(e)
        }), 500


@app.route('/api/save-extracted-bet', methods=['POST'])
@login_required
def save_extracted_bet():
    """Save bet data extracted from OCR to database"""
    try:
        ocr_data = request.json
        if not ocr_data:
            return jsonify({'error': 'No data provided'}), 400
        
        app.logger.info(f"[OCR-SAVE] Saving extracted bet for user {current_user.username}")
        
        # Convert OCR format to bet_data format
        bet_data = convert_ocr_to_bet_format(ocr_data)
        
        # Save to database
        saved_bet = save_bet_to_db(current_user.id, bet_data)
        
        app.logger.info(f"[OCR-SAVE] ✓ Saved bet {saved_bet['bet_id']} with {len(saved_bet.get('legs', []))} legs")
        
        return jsonify({
            'success': True,
            'bet': saved_bet,
            'message': f'Bet saved successfully! {len(saved_bet.get("legs", []))} legs added.'
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"[OCR-SAVE] Error saving extracted bet: {e}")
        return jsonify({
            'error': 'Failed to save bet',
            'details': str(e)
        }), 500


def convert_ocr_to_bet_format(ocr_data):
    """Convert OCR extracted data to the format expected by save_bet_to_db()
    
    OCR format:
    {
      "bet_site": "DraftKings",
      "bet_type": "parlay",
      "total_odds": "+450",
      "wager_amount": 25.00,
      "potential_payout": 137.50,
      "bet_date": "2024-11-12",
      "legs": [...]
    }
    
    Bet format:
    {
      "bet_id": "ocr_12345",
      "type": "parlay",
      "betting_site": "DraftKings",
      "bet_date": "2024-11-12",
      "stake": 25.00,
      "potential_return": 137.50,
      "american_odds": "+450",
      "legs": [...]
    }
    """
    import uuid
    from datetime import datetime
    
    # Generate unique bet ID
    bet_id = f"ocr_{uuid.uuid4().hex[:8]}"
    
    # Convert legs
    converted_legs = []
    for i, leg in enumerate(ocr_data.get('legs', [])):
        converted_leg = {
            'sport': leg.get('sport', 'NFL'),
            'player': leg.get('player_name'),
            'team': leg.get('team_name'),
            'home_team': leg.get('home_team'),
            'away_team': leg.get('away_team'),
            'game_info': leg.get('game_info'),
            'game_date': leg.get('game_date'),
            'type': leg.get('bet_type', 'player_prop'),
            'stat': leg.get('stat_type'),
            'line': leg.get('target_value'),
            'over_under': leg.get('bet_line_type'),  # "over" or "under"
            'odds': leg.get('odds', '-110'),
            'status': 'pending',  # New bets start as pending
            'leg_order': i
        }
        
        # Clean up None values
        converted_leg = {k: v for k, v in converted_leg.items() if v is not None}
        
        converted_legs.append(converted_leg)
    
    # Build bet data
    bet_data = {
        'bet_id': bet_id,
        'type': ocr_data.get('bet_type', 'parlay'),
        'betting_site': ocr_data.get('bet_site', 'Unknown'),
        'bet_date': ocr_data.get('bet_date') or datetime.now().strftime('%Y-%m-%d'),
        'stake': ocr_data.get('wager_amount', 0),
        'potential_return': ocr_data.get('potential_payout', 0),
        'american_odds': ocr_data.get('total_odds'),
        'legs': converted_legs,
        'status': 'pending',  # New bet starts as pending
        'source': 'ocr',  # Mark as OCR-sourced for tracking
        'notes': f'Uploaded via OCR on {datetime.now().strftime("%Y-%m-%d %H:%M")}'
    }
    
    return bet_data


@app.route('/')
def index():
    """Serve the main app page - must be public for PWA to work"""
    return send_from_directory('.', 'index.html')

@app.route('/login.html')
def login_page():
    """Serve the login page"""
    return send_from_directory('.', 'login.html')

@app.route('/register.html')
def register_page():
    """Serve the register page (admin only)"""
    return send_from_directory('.', 'register.html')

@app.route('/pwa-debug.html')
def pwa_debug():
    """Serve PWA debug page"""
    return send_from_directory('.', 'pwa-debug.html')

# PWA Support - These routes must be public for PWA to work
@app.route('/manifest.json')
def manifest():
    """Serve PWA manifest file"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        response = send_from_directory(base_dir, 'manifest.json')
        response.headers['Content-Type'] = 'application/manifest+json'
        response.headers['Cache-Control'] = 'public, max-age=0, must-revalidate'
        return response
    except Exception as e:
        app.logger.error(f"Error serving manifest: {e}")
        return jsonify({"error": "Manifest not found"}), 404

@app.route('/service-worker.js')
def service_worker():
    """Serve service worker file"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        response = send_from_directory(base_dir, 'service-worker.js')
        response.headers['Content-Type'] = 'application/javascript; charset=utf-8'
        response.headers['Cache-Control'] = 'public, max-age=0, must-revalidate'
        response.headers['Service-Worker-Allowed'] = '/'
        return response
    except Exception as e:
        app.logger.error(f"Error serving service worker: {e}")
        return jsonify({"error": "Service worker not found"}), 404

@app.route('/media/icons/<path:filename>')
def serve_icon(filename):
    """Serve app icons for PWA"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        icons_path = os.path.join(base_dir, 'media', 'icons')
        return send_from_directory(icons_path, filename, mimetype='image/png')
    except Exception as e:
        app.logger.error(f"Error serving icon {filename}: {e}")
        return jsonify({"error": "Icon not found"}), 404

@app.route('/media/logos/<path:filename>')
def serve_logo(filename):
    """Serve logo files"""
    return send_from_directory('media/logos', filename)

@app.route('/media/<path:filename>')
def serve_media(filename):
    """Serve other media files"""
    return send_from_directory('media', filename)

@app.route("/admin/fix-duplicate-leg/<bet_db_id>")
@login_required
def fix_duplicate_leg(bet_db_id):
    """Remove duplicate legs from a bet"""
    try:
        bet = Bet.query.get(int(bet_db_id))
        if not bet:
            return jsonify({"error": "Bet not found"}), 404
        
        # Parse bet_data if it's a string
        bet_data = bet.bet_data
        if isinstance(bet_data, str):
            bet_data = json.loads(bet_data)
        
        original_count = len(bet_data.get('legs', []))
        
        # Remove duplicates based on player, stat, target, and stat_add
        seen_legs = []
        unique_legs = []
        duplicates = []
        
        for leg in bet_data.get('legs', []):
            leg_key = (leg.get('player'), leg.get('stat'), leg.get('target'), leg.get('stat_add'))
            if leg_key not in seen_legs:
                seen_legs.append(leg_key)
                unique_legs.append(leg)
            else:
                duplicates.append(f"{leg.get('player')} - {leg.get('stat')} {leg.get('target')}")
        
        if len(duplicates) == 0:
            return jsonify({"message": "No duplicates found", "leg_count": original_count})
        
        # Update bet data
        bet_data['legs'] = unique_legs
        bet.bet_data = bet_data
        db.session.commit()
        
        return jsonify({
            "message": "Duplicates removed",
            "original_legs": original_count,
            "current_legs": len(unique_legs),
            "removed": duplicates
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def update_team_data_on_startup():
    """Update team records on application startup (runs in background)"""
    import subprocess
    import threading
    
    def run_update():
        try:
            app.logger.info("Starting background team data update...")
            result = subprocess.run(
                ['python', 'update_team_records.py'],
                cwd=os.path.dirname(__file__),
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            if result.returncode == 0:
                app.logger.info("Team data update completed successfully")
            else:
                app.logger.warning(f"Team data update failed: {result.stderr}")
        except Exception as e:
            app.logger.error(f"Error updating team data: {e}")
    
    # Run in background thread so it doesn't block startup
    thread = threading.Thread(target=run_update, daemon=True)
    thread.start()

if __name__ == "__main__":
    # Initialize database tables
    with app.app_context():
        db.create_all()
        app.logger.info("Database tables created/verified")
        
        # Update team data on startup (runs in background)
        update_team_data_on_startup()
        
        # Normalize team names in bet_legs table
        normalize_bet_leg_team_names()
        
        # Schedule automated bet leg updates every 5 minutes
        # This updates achieved_value and status for completed bets when games become final
        def run_scheduled_update():
            with app.app_context():
                update_completed_bet_legs()
        
        scheduler.add_job(
            func=run_scheduled_update,
            trigger=IntervalTrigger(minutes=5),
            id='update_bet_legs',
            name='Update completed bet legs with final results',
            replace_existing=True
        )
        app.logger.info("✓ Scheduled automated bet leg updates (every 5 minutes)")
    
    # Initialize and organize parlays before starting server
    # Note: This is legacy code for JSON files, will be phased out
    try:
        initialize_parlay_files()
    except Exception as e:
        app.logger.warning(f"Legacy parlay initialization failed (expected after migration): {e}")
    
    # Run without the debug reloader during automated tests to avoid restarts
    app.run(debug=False, port=5001)