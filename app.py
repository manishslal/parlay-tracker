# app.py - Parlay Tracker Backend
# Force redeploy: 2025-10-20 19:30
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
from datetime import datetime
import json

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
from flask import request

# Configure Flask to serve static files from root directory
app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Decorator to require admin token for all endpoints
def require_admin_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        admin_token = os.environ.get('ADMIN_TOKEN')
        if not admin_token:
            return jsonify({"error": "ADMIN_TOKEN not configured on server"}), 500
        # Accept token in header X-Admin-Token or in JSON body as `token` (for POST)
        token = request.headers.get('X-Admin-Token')
        if not token and request.method == 'POST':
            try:
                body = request.get_json(force=True, silent=True) or {}
                token = body.get('token')
            except Exception:
                token = None
        if token != admin_token:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

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


@app.route("/live")
@require_admin_token
def live():
    live_parlays = load_live_parlays()
    processed = process_parlay_data(live_parlays)
    return jsonify(sort_parlays_by_date(processed))



@app.route("/todays")
@require_admin_token
def todays():
    todays_parlays = load_parlays()
    # Return the raw today's bets (we want to show what's still in Todays_Bets.json)
    processed = process_parlay_data(todays_parlays)
    return jsonify(sort_parlays_by_date(processed))

@app.route("/historical")
@require_admin_token
def historical():
    try:
        app.logger.info("Starting historical endpoint processing")
        
        # Load historical parlays
        try:
            historical_parlays = load_historical_bets()
            app.logger.info(f"Loaded {len(historical_parlays)} historical parlays")
            for parlay in historical_parlays:
                app.logger.info(f"Parlay: {parlay.get('name')}, type: {parlay.get('type')}, legs: {len(parlay.get('legs', []))}")
        except Exception as e:
            app.logger.error(f"Error loading historical bets: {str(e)}")
            raise
            
        if not historical_parlays:
            app.logger.warning("No historical parlays found")
            return jsonify([])
            
        # Process parlays
        try:
            processed = process_parlay_data(historical_parlays)
            app.logger.info(f"Processed {len(processed)} historical parlays")
            for p in processed:
                app.logger.info(f"Processed parlay: {p.get('name')}")
        except Exception as e:
            app.logger.error(f"Error processing parlays: {str(e)}")
            raise
        
        # Sort and return
        try:
            sorted_parlays = sort_parlays_by_date(processed)
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
@require_admin_token
def stats():
    # Clear game data cache to force fresh ESPN API calls
    global game_data_cache
    game_data_cache = {}
    
    parlays = load_parlays()
    processed_parlays = process_parlay_data(parlays)
    
    # DON'T process/move parlays on every stats request - that clears Live_Bets.json!
    # process_parlays(processed_parlays)
    
    # Return processed live parlays for display
    live_parlays = load_live_parlays()
    processed_live = process_parlay_data(live_parlays)
    return jsonify(sort_parlays_by_date(processed_live))

@app.route('/admin/compute_returns', methods=['POST'])
@require_admin_token
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
@require_admin_token
def admin_move_completed():
    """Admin endpoint to move completed games from Todays_Bets and Live_Bets to Historical_Bets.
    Checks ESPN API to see which games are STATUS_FINAL and moves them.
    Returns a JSON summary of what was moved.
    """
    try:
        # Load from BOTH Todays_Bets.json and Live_Bets.json
        today_parlays = load_parlays()  # Loads Todays_Bets.json
        live_parlays = load_live_parlays()  # Loads Live_Bets.json
        historical_parlays = load_historical_bets()
        
        moved_parlays = []
        remaining_today = []
        remaining_live = []
        
        # Create set of existing historical parlay IDs to prevent duplicates
        existing_historical = {f"{p['name']}_{p.get('bet_id', '')}_{p['legs'][0]['game_date']}" 
                             for p in historical_parlays if p.get('legs')}
        
        # Check each parlay from Todays_Bets.json
        for parlay in today_parlays:
            if not parlay.get('legs'):
                remaining_today.append(parlay)
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
                        # If we get here, game is FINAL - keep checking other legs
                        break  # Break out of events loop, continue to next leg
                
                # If we never found this game in the events, it's not complete
                if not found_game:
                    app.logger.warning(f"[Todays_Bets] Game not found in events: {leg['away']} @ {leg['home']} on {game_date}")
                    all_games_complete = False
                    break
                
                if not all_games_complete:
                    break
            
            # Move to historical if complete
            parlay_id = f"{parlay['name']}_{parlay.get('bet_id', '')}_{parlay['legs'][0]['game_date']}"
            if all_games_complete and parlay_id not in existing_historical:
                historical_parlays.append(parlay)
                moved_parlays.append(parlay['name'])
                existing_historical.add(parlay_id)  # Prevent duplicates in same operation
                app.logger.info(f"Moving completed parlay from Todays_Bets to historical: {parlay['name']}")
            else:
                if not all_games_complete:
                    app.logger.debug(f"[Todays_Bets] Parlay not complete: {parlay['name']}")
                remaining_today.append(parlay)
        
        # Check each parlay from Live_Bets.json
        for parlay in live_parlays:
            if not parlay.get('legs'):
                remaining_live.append(parlay)
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
                        # If we get here, game is FINAL - keep checking other legs
                        break  # Break out of events loop, continue to next leg
                
                # If we never found this game in the events, it's not complete
                if not found_game:
                    app.logger.warning(f"[Live_Bets] Game not found in events: {leg['away']} @ {leg['home']} on {game_date}")
                    all_games_complete = False
                    break
                
                if not all_games_complete:
                    break
            
            # Move to historical if complete
            parlay_id = f"{parlay['name']}_{parlay.get('bet_id', '')}_{parlay['legs'][0]['game_date']}"
            if all_games_complete and parlay_id not in existing_historical:
                historical_parlays.append(parlay)
                moved_parlays.append(parlay['name'])
                existing_historical.add(parlay_id)  # Prevent duplicates in same operation
                app.logger.info(f"Moving completed parlay from Live_Bets to historical: {parlay['name']}")
            else:
                if not all_games_complete:
                    app.logger.debug(f"[Live_Bets] Parlay not complete: {parlay['name']}")
                remaining_live.append(parlay)
        
        # Save updated files (ALL THREE)
        save_parlays(sort_parlays_by_date(historical_parlays), data_path("Historical_Bets.json"))
        save_parlays(sort_parlays_by_date(remaining_today), data_path("Todays_Bets.json"))
        save_parlays(sort_parlays_by_date(remaining_live), data_path("Live_Bets.json"))
        
        total_remaining = len(remaining_today) + len(remaining_live)
        
        return jsonify({
            "moved": moved_parlays,
            "moved_count": len(moved_parlays),
            "remaining_live": total_remaining,
            "remaining_today": len(remaining_today),
            "remaining_live_only": len(remaining_live)
        })
    except Exception as e:
        app.logger.error(f"Error in admin_move_completed: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/admin/export_files', methods=['GET'])
@require_admin_token
def admin_export_files():
    """Admin endpoint to export all data files as JSON.
    Returns all three files (Live, Todays, Historical) in one response.
    Use this to sync remote state back to local.
    """
    try:
        return jsonify({
            "live_bets": load_live_parlays(),
            "todays_bets": load_parlays(),
            "historical_bets": load_historical_bets()
        })
    except Exception as e:
        app.logger.error(f"Error in admin_export_files: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    """Serve the main app page - must be public for PWA to work"""
    return send_from_directory('.', 'index.html')

@app.route('/pwa-debug.html')
def pwa_debug():
    """Serve PWA debug page"""
    return send_from_directory('.', 'pwa-debug.html')

# PWA Support - These routes must be public for PWA to work
@app.route('/manifest.json')
def manifest():
    """Serve PWA manifest file"""
    response = send_from_directory('.', 'manifest.json')
    response.headers['Content-Type'] = 'application/manifest+json'
    response.headers['Cache-Control'] = 'public, max-age=0, must-revalidate'
    return response

@app.route('/service-worker.js')
def service_worker():
    """Serve service worker file"""
    response = send_from_directory('.', 'service-worker.js')
    response.headers['Content-Type'] = 'application/javascript; charset=utf-8'
    response.headers['Cache-Control'] = 'public, max-age=0, must-revalidate'
    response.headers['Service-Worker-Allowed'] = '/'
    return response

@app.route('/media/icons/<path:filename>')
def serve_icon(filename):
    """Serve app icons for PWA"""
    return send_from_directory('media/icons', filename, mimetype='image/png')

@app.route('/media/logos/<path:filename>')
def serve_logo(filename):
    """Serve logo files"""
    return send_from_directory('media/logos', filename)

@app.route('/media/<path:filename>')
def serve_media(filename):
    """Serve other media files"""
    return send_from_directory('media', filename)

if __name__ == "__main__":
    # Initialize and organize parlays before starting server
    initialize_parlay_files()
    # Run without the debug reloader during automated tests to avoid restarts
    app.run(debug=False, port=5001)