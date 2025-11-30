import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")

def data_path(filename: str) -> str:
    return os.path.join(DATA_DIR, filename)
import re
from datetime import datetime
from typing import Any, List, Optional
import requests
import difflib
import logging

logger = logging.getLogger(__name__)

def parse_american_odds(odds):
    """Parse American odds like +150 or -120 and return decimal multiplier (including stake)."""
    if odds is None:
        return None
    try:
        s = str(odds).strip()
        if s == "":
            return None
        if s.startswith("+"):
            val = int(s[1:])
            return 1 + (val / 100.0)
        if s.startswith("-"):
            val = int(s[1:])
            if val == 0:
                return None
            return 1 + (100.0 / val)
        if s.isdigit() or (s[0] == '-' and s[1:].isdigit()):
            val = int(s)
            if val > 0:
                return 1 + (val / 100.0)
            else:
                return 1 + (100.0 / abs(val))
        f = float(s)
        if f > 0:
            return f
    except Exception:
        return None
    return None

def compute_parlay_returns_from_odds(wager, parlay_odds=None, leg_odds_list=None):
    """Compute expected profit (returns) from wager and odds."""
    try:
        if wager is None:
            return None
        w = float(wager)
        if parlay_odds:
            mult = parse_american_odds(parlay_odds)
            if mult is None:
                return None
            return round(w * (mult - 1), 2)
        if leg_odds_list:
            mult = 1.0
            any_parsed = False
            for o in leg_odds_list:
                pm = parse_american_odds(o)
                if pm is None:
                    continue
                any_parsed = True
                mult *= pm
            if any_parsed:
                return round(w * (mult - 1), 2)
        return None
    except Exception:
        return None

def sort_parlays_by_date(parlays):
    def get_latest_date(parlay):
        dates = [leg.get('game_date') or '1900-01-01' for leg in parlay.get('legs', []) if leg.get('game_date')]
        return max(dates) if dates else '1900-01-01'
    return sorted(parlays, key=get_latest_date, reverse=True)

def get_events(date_str, sport='NFL'):
    """Fetch events from ESPN API for a given date and sport."""
    d = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y%m%d")
    sport_map = {
        'NFL': 'football/nfl',
        'NBA': 'basketball/nba',
        'MLB': 'baseball/mlb',
        'NHL': 'hockey/nhl',
        'NCAAF': 'football/college-football',
        'NCAAB': 'basketball/mens-college-basketball'
    }
    sport_path = sport_map.get(sport.upper(), 'football/nfl')
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/scoreboard?dates={d}"
    try:
        # Try with SSL verification first
        data = requests.get(url, timeout=10, verify=True).json()
        return data.get("events", [])
    except requests.exceptions.SSLError as ssl_err:
        logger.warning(f"SSL error fetching ESPN API for {d}: {ssl_err}. Retrying without SSL verification...")
        try:
            # Retry without SSL verification as fallback
            data = requests.get(url, timeout=10, verify=False).json()
            logger.info(f"Successfully fetched ESPN data without SSL verification for {d}")
            return data.get("events", [])
        except Exception as e:
            logger.warning(f"Failed to fetch events from ESPN API for {d} (even without SSL verification): {e}")
            return []
    except Exception as e:
        logger.warning(f"Failed to fetch events from ESPN API for {d}: {e}")
        return []

def _norm(s):
    return re.sub(r"[^a-z0-9 ]+", "", s.lower()).strip()

def _get_player_stat_from_boxscore(player_name, category_name, stat_label, boxscore):
    player_norm = _norm(player_name)
    for team_box in boxscore:
        for cat in team_box.get("statistics", []):
            # ESPN API returns 'None' as a string for NBA stats, treat as empty category
            cat_name = cat.get("name", "")
            cat_name_normalized = "" if cat_name in ["None", None, ""] else cat_name
            category_name_normalized = "" if category_name in ["None", None, ""] else category_name
            
            if cat_name_normalized.lower() == category_name_normalized.lower():
                try:
                    labels = [l for l in cat.get("labels", [])]
                    if stat_label not in labels:
                        continue
                    stat_idx = labels.index(stat_label)
                    for ath in cat.get("athletes", []):
                        ath_name_raw = ath.get("athlete", {}).get("displayName", "")
                        ath_name = _norm(ath_name_raw)
                        if all(tok in ath_name for tok in player_norm.split()):
                            stats = ath.get("stats", [])
                            if stat_idx < len(stats):
                                val = stats[stat_idx]
                                # Handle "made-attempted" format (e.g., "2-5") common in NBA stats
                                if isinstance(val, str) and "-" in val:
                                    try:
                                        return int(val.split("-")[0])
                                    except:
                                        pass
                                # Handle "made/attempted" format (e.g., "4/4") common in NFL kicking
                                if isinstance(val, str) and "/" in val:
                                    try:
                                        return int(val.split("/")[0])
                                    except:
                                        pass
                                try:
                                    return int(float(val))
                                except Exception:
                                    return 0
                    try:
                        # Fuzzy matching fallback - use normalized names for consistency
                        athlete_names_raw = [a.get('athlete', {}).get('displayName', '') for a in cat.get('athletes', [])]
                        athlete_names_norm = [_norm(name) for name in athlete_names_raw]
                        
                        # First try substring matching (e.g. "Mahomes" in "Patrick Mahomes II")
                        match_idx = -1
                        for idx, name in enumerate(athlete_names_norm):
                            if player_norm in name or name in player_norm:
                                match_idx = idx
                                break
                        
                        # Try First Initial + Last Name matching (e.g. "J. Gibbs" -> "Jahmyr Gibbs")
                        if match_idx == -1:
                            # Extract initial and last name from search query
                            parts = player_norm.split()
                            if len(parts) >= 2 and len(parts[0]) == 1:
                                initial = parts[0]
                                lastname = parts[-1]
                                for idx, name in enumerate(athlete_names_norm):
                                    name_parts = name.split()
                                    if len(name_parts) >= 2:
                                        # Check if initial matches first char of first name AND lastname matches
                                        if name_parts[0].startswith(initial) and lastname in name_parts[-1]:
                                            match_idx = idx
                                            break

                        # If no substring match, try fuzzy matching
                        if match_idx == -1:
                            matches = difflib.get_close_matches(player_norm, athlete_names_norm, n=1, cutoff=0.75)
                            if matches:
                                best_norm = matches[0]
                                match_idx = athlete_names_norm.index(best_norm)
                        
                        if match_idx != -1:
                            ath = cat.get('athletes', [])[match_idx]
                            stats = ath.get('stats', [])
                            if stat_idx < len(stats):
                                val = stats[stat_idx]
                                # Handle "made-attempted" format (e.g., "2-5") common in NBA stats
                                if isinstance(val, str) and "-" in val:
                                    try:
                                        return int(val.split("-")[0])
                                    except:
                                        pass
                                # Handle "made/attempted" format (e.g., "4/4") common in NFL kicking
                                if isinstance(val, str) and "/" in val:
                                    try:
                                        return int(val.split("/")[0])
                                    except:
                                        pass
                                try:
                                    return int(float(val))
                                except Exception:
                                    return 0
                    except Exception:
                        pass
                except (ValueError, IndexError):
                    continue
    return None

def _get_touchdowns(player_name, boxscore, scoring_plays=None):
    td_cats = {
        "rushing": "TD", "receiving": "TD",
        "interception": "TD", "kickoffReturn": "TD", "puntReturn": "TD",
        "fumbleReturn": "TD"
    }
    total_tds = 0
    for cat, label in td_cats.items():
        val = _get_player_stat_from_boxscore(player_name, cat, label, boxscore)
        if val is not None:
            total_tds += val
    if total_tds > 0:
        return total_tds
    if scoring_plays:
        player_norm = _norm(player_name)
        td_count = 0
        for play in scoring_plays:
            participants = play.get("participants")
            # If participants is present (scoreboard endpoint), use it
            if participants:
                for p in participants:
                    name = p.get("displayName") or p.get("athlete", {}).get("displayName")
                    if name and player_norm in _norm(name):
                        td_count += 1
                        break
            # Fallback: Check text description if participants is missing (summary endpoint)
            # Text format: "Player Name 1 Yd Run..."
            else:
                text = play.get("text", "")
                if text:
                    text_norm = _norm(text)
                    # Check if player name is in the text
                    # We use a stricter check here to avoid false positives
                    if player_norm in text_norm:
                        # Special handling for Passing TDs to avoid counting the passer
                        # If play type is "Passing Touchdown", the text usually starts with the passer's name
                        # e.g. "Sam Darnold 5 Yd Pass to..."
                        play_type = play.get("type", {}).get("text", "")
                        if "Passing Touchdown" in play_type:
                            if text_norm.startswith(player_norm):
                                continue
                        
                        td_count += 1
        return td_count
    return total_tds

def calculate_bet_value(bet, game_data):
    stat = bet["stat"].strip().lower()
    boxscore = game_data.get("boxscore", [])
    scoring_plays = game_data.get("scoring_plays", [])
    if "player" in bet:
        player_name = bet["player"]
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
    if stat == "moneyline":
        if "team" not in bet:
            return 0
        bet_team = bet["team"]
        home_team = game_data["teams"]["home"]
        away_team = game_data["teams"]["away"]
        bet_team_norm = bet_team.lower().strip()
        home_team_norm = home_team.lower().strip()
        away_team_norm = away_team.lower().strip()
        if (bet_team_norm == home_team_norm or bet_team_norm in home_team_norm or home_team_norm in bet_team_norm):
            score_diff = home_score - away_score
        elif (bet_team_norm == away_team_norm or bet_team_norm in away_team_norm or away_team_norm in bet_team_norm):
            score_diff = away_score - home_score
        else:
            return 0
        return score_diff
    if stat == "spread":
        if "team" not in bet:
            return 0
        bet_team = bet["team"]
        home_team = game_data["teams"]["home"]
        away_team = game_data["teams"]["away"]
        spread = bet.get("target", 0)
        bet_team_norm = bet_team.lower().strip()
        home_team_norm = home_team.lower().strip()
        away_team_norm = away_team.lower().strip()
        if (bet_team_norm == home_team_norm or bet_team_norm in home_team_norm or home_team_norm in bet_team_norm):
            score_diff = home_score - away_score
        elif (bet_team_norm == away_team_norm or bet_team_norm in away_team_norm or away_team_norm in bet_team_norm):
            score_diff = away_score - home_score
        else:
            return 0
        return score_diff
    return 0
