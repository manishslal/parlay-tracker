# app.py - Parlay Tracker Backend - Multi-User Edition
# Force redeploy: 2025-11-01 00:00
from flask import Flask, jsonify, send_from_directory, request, session, redirect, url_for
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import requests
import os
from datetime import datetime
import json

# Import database models
from models import db, User, Bet

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

# Configure Flask to serve static files from root directory
app = Flask(__name__, static_folder='.', static_url_path='')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///parlays.db')
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

def save_final_results_to_bet(bet, processed_data):
    """Save final game results to bet data when games are completed
    
    This preserves final scores and outcomes so we don't lose data when ESPN
    removes old games from their API.
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
        
        # Update each leg with final results
        updated = False
        for i, leg in enumerate(bet_data.get('legs', [])):
            # Find matching leg in processed data
            if i < len(matching_parlay.get('legs', [])):
                processed_leg = matching_parlay['legs'][i]
                
                # Save final stats if game is complete
                if processed_leg.get('game_status') == 'STATUS_FINAL':
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
    """Automatically move bets to 'completed' status when all their games have ended
    
    Also saves final game results before moving to completed status.
    """
    try:
        from datetime import date
        today = date.today()
        
        # Get all pending and live bets for user
        bets = get_user_bets_from_db(user_id, status_filter=['pending', 'live'])
        
        # First, process all bets to get current data from ESPN
        bet_data_list = [bet.get_bet_data() for bet in bets]
        processed_data = process_parlay_data(bet_data_list)
        
        updated_count = 0
        for bet in bets:
            bet_data = bet.get_bet_data()
            legs = bet_data.get('legs', [])
            
            if not legs:
                continue
            
            # Check if all games have ended (all game_dates are in the past)
            all_games_ended = True
            for leg in legs:
                game_date_str = leg.get('game_date', '')
                if game_date_str:
                    try:
                        # Parse game date (format: YYYY-MM-DD)
                        game_date = datetime.strptime(game_date_str, '%Y-%m-%d').date()
                        # If game date is today or future, games haven't ended
                        if game_date >= today:
                            all_games_ended = False
                            break
                    except ValueError:
                        # If date parsing fails, skip this leg
                        continue
            
            # If all games have ended, save final results and move to completed
            if all_games_ended and legs:  # Make sure there are legs to check
                app.logger.info(f"Auto-moving bet {bet.id} to completed (all games ended)")
                
                # Save final results before marking as completed
                save_final_results_to_bet(bet, processed_data)
                
                bet.status = 'completed'
                updated_count += 1
        
        # Commit all changes at once
        if updated_count > 0:
            db.session.commit()
            app.logger.info(f"Auto-moved {updated_count} bets to completed status with final results")
            
    except Exception as e:
        app.logger.error(f"Error auto-moving completed bets: {e}")
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

def get_events(date_str):
    app.logger.info(f"Fetching events for date: {date_str}")
    # Mock data disabled - prefer real ESPN responses for accuracy. If you need
    # mock data for offline testing, re-enable or modify the block below.
    #
    # if date_str == "2025-10-13":
    #     app.logger.info("Using mock data for 2025-10-13")
    #     return mock_data
    
    # For other dates, try the real API
    d = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y%m%d")
    url = f"http://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={d}"
    try:
        data = requests.get(url).json()
        return data.get("events", [])
    except Exception as e:
        app.logger.error(f"Failed to fetch events for {date_str}: {e}")
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
    stat = bet["stat"]
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
        
        # Determine if the bet team won
        if bet_team == home_team:
            return 1 if home_score > away_score else 0
        elif bet_team == away_team:
            return 1 if away_score > home_score else 0
        else:
            return 0
    
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
        
        # Calculate the score difference from bet team's perspective
        if bet_team == home_team:
            score_diff = home_score - away_score
        elif bet_team == away_team:
            score_diff = away_score - home_score
        else:
            return 0
        
        # For spread: if target is -7, team needs to win by more than 7
        # If target is +7, team can lose by up to 7 and still cover
        # The bet wins if: score_diff > spread (for negative spreads)
        # or score_diff >= -spread (for positive spreads)
        # Simplified: score_diff + spread > 0
        return 1 if score_diff + spread > 0 else 0

    return 0 # Default for unhandled stats

def fetch_game_details_from_espn(game_date, away_team, home_team):
    """Fetch detailed game data for a single game."""
    try:
        app.logger.info(f"Fetching game details for {away_team} @ {home_team} on {game_date}")
        events = get_events(game_date)
        app.logger.info(f"Found {len(events)} events for {game_date}")
        
        ev = None
        for event in events:
            try:
                team_names = {c['team']['displayName'] for c in event['competitions'][0]['competitors']}
                app.logger.info(f"Event team names: {team_names}")
                if away_team in team_names and home_team in team_names:
                    ev = event
                    app.logger.info("Found matching event")
                    break
            except Exception as e:
                app.logger.error(f"Error processing event: {str(e)}")
                continue
                
        if not ev:
            app.logger.warning(f"No matching event found for {away_team} @ {home_team}")
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
                summary_url = f"http://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={ev['id']}"
                app.logger.info(f"Fetching summary for event {ev['id']}: {summary_url}")
                summary = requests.get(summary_url, timeout=8).json()
                # summary may use camelCase keys
                s_box = summary.get("boxscore") or summary.get("boxScore") or {}
                boxscore_players = s_box.get("players") or []
                scoring_plays = summary.get("scoringPlays") or summary.get("scoring_plays") or []
                app.logger.info(f"Summary fetched: box players={len(boxscore_players)}, scoring plays={len(scoring_plays)}")
            except Exception as e:
                app.logger.error(f"Error fetching summary for event {ev.get('id')}: {e}")

        game = {
            "espn_game_id": ev["id"],
            "teams": {"away": away["team"]["displayName"], "home": home["team"]["displayName"]},
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
            game_key = f"{leg['game_date']}_{leg['away']}_{leg['home']}"
            app.logger.info(f"Game key: {game_key}")
            
            if game_key not in game_data_cache:
                app.logger.info(f"Fetching game data for {game_key}")
                game_data = fetch_game_details_from_espn(leg['game_date'], leg['away'], leg['home'])
                app.logger.info(f"Game data fetched: {game_data is not None}")
                game_data_cache[game_key] = game_data
            else:
                app.logger.info(f"Using cached game data for {game_key}")
            
            if game_data_cache.get(game_key):
                app.logger.info(f"Adding game data to parlay_games: {game_key}")
                parlay_games[game_key] = game_data_cache[game_key]
            else:
                app.logger.warning(f"No game data available for {game_key}")

        for leg in parlay.get("legs", []):
            app.logger.info(f"Processing leg in final stage: {leg}")
            game_key = f"{leg['game_date']}_{leg['away']}_{leg['home']}"
            game_data = parlay_games.get(game_key)
            app.logger.info(f"Game data for {game_key}: {game_data is not None}")
            
            leg["parlay_name"] = parlay.get("name", "Unknown Bet")

            if game_data:
                try:
                    leg["current"] = calculate_bet_value(leg, game_data)
                    app.logger.info(f"Calculated value for {leg.get('player', leg.get('team', 'Unknown'))} - {leg['stat']}: {leg['current']}")
                    
                    # Add score differential for spread/moneyline bets
                    if leg["stat"] in ["spread", "moneyline"]:
                        home_score = game_data.get("score", {}).get("home", 0)
                        away_score = game_data.get("score", {}).get("away", 0)
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
                app.logger.warning(f"No game data found for {game_key}")
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
    
    # Check if user already exists
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    try:
        user = User(username=username, email=email)
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
    """Login with username/email and password"""
    data = request.json
    identifier = data.get('username') or data.get('email')
    password = data.get('password')
    
    if not identifier or not password:
        return jsonify({'error': 'Missing credentials'}), 400
    
    # Try to find user by username or email
    user = User.query.filter(
        (User.username == identifier) | (User.email == identifier)
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
    # Get live bets from database for current user
    bets = get_user_bets_from_db(current_user.id, status_filter='live')
    # Convert Bet objects to dict format compatible with existing frontend
    live_parlays = [bet.get_bet_data() for bet in bets]
    processed = process_parlay_data(live_parlays)
    return jsonify(sort_parlays_by_date(processed))



@app.route("/todays")
@login_required
def todays():
    # Auto-move completed bets (games that have ended)
    auto_move_completed_bets(current_user.id)
    
    # Get today's bets from database for current user
    bets = get_user_bets_from_db(current_user.id, status_filter='pending')
    todays_parlays = [bet.get_bet_data() for bet in bets]
    # Return the raw today's bets
    processed = process_parlay_data(todays_parlays)
    return jsonify(sort_parlays_by_date(processed))

@app.route("/historical")
@login_required
def historical():
    try:
        app.logger.info("Starting historical endpoint processing")
        
        # Load historical parlays from database for current user
        try:
            bets = get_user_bets_from_db(current_user.id, status_filter='completed')
            historical_parlays = [bet.get_bet_data() for bet in bets]
            app.logger.info(f"Loaded {len(historical_parlays)} historical parlays")
            for parlay in historical_parlays:
                app.logger.info(f"Parlay: {parlay.get('name')}, type: {parlay.get('type')}, legs: {len(parlay.get('legs', []))}")
        except Exception as e:
            app.logger.error(f"Error loading historical bets: {str(e)}")
            raise
            
        if not historical_parlays:
            app.logger.warning("No historical parlays found")
            return jsonify([])
        
        # Separate bets with saved final results from those needing ESPN fetch
        bets_with_finals = []
        bets_needing_fetch = []
        
        for parlay in historical_parlays:
            has_final_results = all(
                leg.get('final_value') is not None or leg.get('result') is not None
                for leg in parlay.get('legs', [])
            )
            
            if has_final_results:
                bets_with_finals.append(parlay)
            else:
                bets_needing_fetch.append(parlay)
        
        app.logger.info(f"Historical bets: {len(bets_with_finals)} with saved finals, {len(bets_needing_fetch)} need ESPN fetch")
            
        # Process only bets that need ESPN data
        processed = []
        if bets_needing_fetch:
            try:
                processed = process_parlay_data(bets_needing_fetch)
                app.logger.info(f"Processed {len(processed)} historical parlays from ESPN")
                for p in processed:
                    app.logger.info(f"Processed parlay: {p.get('name')}")
            except Exception as e:
                app.logger.error(f"Error processing parlays from ESPN: {str(e)}")
                # Continue with just the bets that have saved finals
        
        # Add bets with saved final results (no ESPN fetch needed)
        all_historical = bets_with_finals + processed
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
        bet = Bet.query.filter_by(id=bet_id, user_id=current_user.id).first()
        if not bet:
            return jsonify({'error': 'Bet not found'}), 404
        
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update bet data
        bet.set_bet_data(data)
        
        # Update other fields if provided
        if 'status' in data:
            bet.status = data['status']
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
        bet = Bet.query.filter_by(id=bet_id, user_id=current_user.id).first()
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

if __name__ == "__main__":
    # Initialize database tables
    with app.app_context():
        db.create_all()
        app.logger.info("Database tables created/verified")
    
    # Initialize and organize parlays before starting server
    # Note: This is legacy code for JSON files, will be phased out
    try:
        initialize_parlay_files()
    except Exception as e:
        app.logger.warning(f"Legacy parlay initialization failed (expected after migration): {e}")
    
    # Run without the debug reloader during automated tests to avoid restarts
    app.run(debug=False, port=5001)