import re
import json
from datetime import datetime

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
        dates = [leg.get('game_date', '1900-01-01') for leg in parlay.get('legs', [])]
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
    url = f"http://site.api.espn.com/apis/site/v2/sports/{sport_path}/scoreboard?dates={d}"
    try:
        data = requests.get(url).json()
        return data.get("events", [])
    except Exception:
        return []

def _norm(s):
    return re.sub(r"[^a-z0-9 ]+", "", s.lower()).strip()

def _get_player_stat_from_boxscore(player_name, category_name, stat_label, boxscore):
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
                        if all(tok in ath_name for tok in player_norm.split()):
                            stats = ath.get("stats", [])
                            if stat_idx < len(stats):
                                try:
                                    return int(float(stats[stat_idx]))
                                except Exception:
                                    return 0
                    try:
                        athlete_names = [a.get('athlete', {}).get('displayName', '') for a in cat.get('athletes', [])]
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
    td_cats = {
        "rushing": "TD", "receiving": "TD",
        "interception": "TD", "kickoffReturn": "TD", "puntReturn": "TD",
        "fumbleReturn": "TD"
    }
    total_tds = 0
    for cat, label in td_cats.items():
        total_tds += _get_player_stat_from_boxscore(player_name, cat, label, boxscore)
    if total_tds > 0:
        return total_tds
    if scoring_plays:
        def _norm(s):
            return re.sub(r"[^a-z0-9 ]+", "", (s or "").lower()).strip()
        player_norm = _norm(player_name)
        td_count = 0
        for play in scoring_plays:
            participants = play.get("participants", [])
            for p in participants:
                name = p.get("displayName") or p.get("athlete", {}).get("displayName")
                if name and player_norm in _norm(name):
                    td_count += 1
                    break
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
