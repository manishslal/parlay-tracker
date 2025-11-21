import json
from helpers.utils import data_path, get_events, _get_player_stat_from_boxscore, _get_touchdowns
from helpers.utils import compute_parlay_returns_from_odds
import requests
import logging

logger = logging.getLogger(__name__)

# Cache for game data to avoid repeated API calls
game_data_cache = {}

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
            "passing_yards": ("passing", "YDS"), "alt_passing_yards": ("passing", "YDS"),
            "pass_attempts": ("passing", "ATT"),
            "pass_completions": ("passing", "COMP"), "passing_touchdowns": ("passing", "TD"),
            "interceptions_thrown": ("passing", "INT"), "longest_pass_completion": ("passing", "LONG"),
            "rushing_yards": ("rushing", "YDS"), "alt_rushing_yards": ("rushing", "YDS"),
            "rushing_attempts": ("rushing", "CAR"),
            "rushing_touchdowns": ("rushing", "TD"), "longest_rush": ("rushing", "LONG"),
            "receiving_yards": ("receiving", "YDS"), "alt_receiving_yards": ("receiving", "YDS"),
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

def fetch_game_details_from_espn(game_date, away_team, home_team, sport='NFL'):
    """Fetch detailed game data for a single game.

    Args:
        game_date: Date string in YYYY-MM-DD format
        away_team: Away team name or abbreviation
        home_team: Home team name or abbreviation
        sport: Sport code (NFL, NBA, MLB, NHL, etc.)
    """
    try:
        # Handle None or empty game_date
        if not game_date:
            logger.debug(f"Skipping game data fetch - no game_date provided for {away_team} @ {home_team}")
            return None

        logger.info(f"Fetching {sport} game details for {away_team} @ {home_team} on {game_date}")
        events = get_events(game_date, sport)
        logger.info(f"Found {len(events)} {sport} events for {game_date}")
        
        ev = None
        for event in events:
            try:
                competitors = event['competitions'][0]['competitors']
                # Get both full names and abbreviations
                team_names = {c['team']['displayName'] for c in competitors}
                team_abbrs = {c['team']['abbreviation'] for c in competitors}
                logger.info(f"Event teams: {team_names} | Abbreviations: {team_abbrs}")
                
                # Match by either full name or abbreviation with flexible matching
                def team_matches(search_team, team_names, team_abbrs):
                    """Check if search_team matches any team, allowing partial matches"""
                    search_lower = search_team.lower().strip()
                    
                    # Check exact matches first
                    if search_team in team_names or search_team in team_abbrs:
                        return True
                    
                    # Check partial matches for team names (e.g., 'Packers' matches 'Green Bay Packers')
                    for name in team_names:
                        if search_lower in name.lower() or name.lower() in search_lower:
                            return True
                    
                    # Check partial matches for abbreviations (e.g., 'Packers' might match 'GB' in some cases)
                    for abbr in team_abbrs:
                        if search_lower == abbr.lower() or abbr.lower() in search_lower:
                            return True
                    
                    return False
                
                away_match = team_matches(away_team, team_names, team_abbrs)
                home_match = team_matches(home_team, team_names, team_abbrs)
                
                if away_match and home_match:
                    ev = event
                    logger.info("Found matching event")
                    break
            except Exception as e:
                logger.error(f"Error processing event: {str(e)}")
                continue
                
        if not ev:
            # Reduce log level for old games - they won't be in ESPN's current events
            logger.debug(f"No matching event found for {away_team} @ {home_team}")
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
                summary_url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/summary?event={ev['id']}"
                logger.info(f"Fetching {sport} summary for event {ev['id']}: {summary_url}")
                summary = requests.get(summary_url, timeout=8).json()
                # summary may use camelCase keys
                s_box = summary.get("boxscore") or summary.get("boxScore") or {}
                boxscore_players = s_box.get("players") or []
                scoring_plays = summary.get("scoringPlays") or summary.get("scoring_plays") or []
                logger.info(f"Summary fetched: box players={len(boxscore_players)}, scoring plays={len(scoring_plays)}")
            except Exception as e:
                logger.error(f"Error fetching {sport} summary for event {ev.get('id')}: {e}")

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
        logger.error(f"Error in fetch_game_details_from_espn: {str(e)}")
        return None

def process_parlay_data(parlays):
    """Process a list of parlays with game data."""
    if not parlays:
        return []
    
    logger.info("Starting process_parlay_data")
    processed_parlays = []
    
    for parlay in parlays:
        logger.info(f"Processing parlay: {parlay.get('name')}")
        parlay_games = {}
        
        for leg in parlay.get("legs", []):
            logger.info(f"Processing leg for {leg.get('player')} - {leg.get('stat')}")
            sport = leg.get('sport', 'NFL')  # Default to NFL if not specified
            game_key = f"{leg['game_date']}_{sport}_{leg['away']}_{leg['home']}"
            logger.info(f"Game key: {game_key}")
            
            if game_key not in game_data_cache:
                game_data = fetch_game_details_from_espn(leg['game_date'], leg['away'], leg['home'], sport)
                game_data_cache[game_key] = game_data
            else:
                game_data = game_data_cache[game_key]
            
            if game_data:
                parlay_games[game_key] = game_data

        for leg in parlay.get("legs", []):
            # Fix target value for moneyline bets (should be 0, not None)
            if leg.get("stat") == "moneyline" and leg.get("target") is None:
                leg["target"] = 0
            
            sport = leg.get('sport', 'NFL')  # Get sport for this leg
            game_key = f"{leg['game_date']}_{sport}_{leg['away']}_{leg['home']}"
            game_data = parlay_games.get(game_key)
            
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
                    
                    # Update leg with ESPN game ID
                    espn_game_id = game_data.get("espn_game_id")
                    if espn_game_id:
                        leg["gameId"] = str(espn_game_id)
                    
                    leg["current"] = calculate_bet_value(leg, game_data)
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
                            logger.info(f"Matched home team: '{bet_team}' == '{home_team}', score_diff = {home_score - away_score}")
                        elif bet_team_norm == away_team_norm or bet_team_norm in away_team_norm or away_team_norm in bet_team_norm:
                            leg["score_diff"] = away_score - home_score
                            logger.info(f"Matched away team: '{bet_team}' == '{away_team}', score_diff = {away_score - home_score}")
                        else:
                            leg["score_diff"] = 0
                            logger.warning(f"NO MATCH for team '{bet_team}' - ESPN has home:'{home_team}' away:'{away_team}'")
                            
                except Exception as e:
                    logger.error(f"Error calculating bet value: {str(e)}")
                    leg["current"] = 0
            else:
                # Reduce log level for historical games - expected for old completed bets
                logger.debug(f"No game data found for {game_key}")
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
                val = compute_parlay_returns_from_odds(parlay_wager, parlay_odds, leg_odds)
                if val is not None:
                    parlay['returns'] = f"{val:.2f}"
            updated.append((parlay.get('name', 'Unnamed'), parlay.get('returns')))
        results[fname] = updated
        try:
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
    return results

# Add more bet-related service functions here
