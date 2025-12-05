"""
ESPN API integration helpers
Functions for fetching NFL game data from ESPN API
"""

import requests
from datetime import datetime, timedelta
from typing import List, Tuple

def get_espn_games_for_date(date: datetime) -> List[Tuple[str, str]]:
    """
    Fetch NFL games from ESPN API for a given date
    Returns list of (away_team, home_team) tuples
    """
    # ESPN scoreboard API
    date_str = date.strftime("%Y%m%d")
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={date_str}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        games = []
        if 'events' in data:
            for event in data['events']:
                if 'competitions' in event and len(event['competitions']) > 0:
                    competition = event['competitions'][0]
                    if 'competitors' in competition and len(competition['competitors']) >= 2:
                        competitors = competition['competitors']
                        # Find home and away teams
                        home_team = None
                        away_team = None
                        for comp in competitors:
                            if comp.get('homeAway') == 'home':
                                home_team = comp['team']['displayName']
                            elif comp.get('homeAway') == 'away':
                                away_team = comp['team']['displayName']
                        
                        if home_team and away_team:
                            games.append((away_team, home_team))
        
        return games
    except Exception as e:
        print(f"Error fetching ESPN data for {date_str}: {e}")
        return []

def get_espn_games_with_ids_for_date(date: datetime) -> List[Tuple[str, str, str, datetime]]:
    """
    Fetch games from ESPN API for a given date (NFL and NBA)
    Returns list of (game_id, away_team, home_team, game_date) tuples
    """
    # ESPN scoreboard API
    date_str = date.strftime("%Y%m%d")
    games = []
    
    # Fetch both NFL and NBA games
    sports = [
        ("football", "nfl"),
        ("basketball", "nba")
    ]
    
    for sport, league in sports:
        url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard?dates={date_str}"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'events' in data:
                for event in data['events']:
                    game_id = event.get('id')
                    if not game_id:
                        continue
                        
                    if 'competitions' in event and len(event['competitions']) > 0:
                        competition = event['competitions'][0]
                        if 'competitors' in competition and len(competition['competitors']) >= 2:
                            competitors = competition['competitors']
                            # Find home and away teams
                            home_team = None
                            away_team = None
                            for comp in competitors:
                                if comp.get('homeAway') == 'home':
                                    home_team = comp['team']['displayName']
                                elif comp.get('homeAway') == 'away':
                                    away_team = comp['team']['displayName']
                            
                            if home_team and away_team:
                                # Return the date passed in as the game date
                                games.append((game_id, away_team, home_team, date))
        
        except Exception as e:
            print(f"Error fetching ESPN data for {sport}/{league} on {date_str}: {e}")
            continue
    
    return games

def find_game_for_team(team: str, bet_date: datetime, search_window_days: int = 7) -> Tuple[str, str, str]:
    """
    Find the game matchup for a team based on bet date using ESPN API
    
    Args:
        team: Team name to search for
        bet_date: Date the bet was placed
        search_window_days: Number of days to search forward (default: 7)
    
    Returns:
        Tuple of (away_team, home_team, game_date)
    """
    # Search within window of bet date
    for days_offset in range(0, search_window_days):
        check_date = bet_date + timedelta(days=days_offset)
        games = get_espn_games_for_date(check_date)
        
        for away, home in games:
            if team == away or team == home:
                return (away, home, check_date.strftime("%Y-%m-%d"))
    
    print(f"Warning: No game found for team {team} around {bet_date.strftime('%Y-%m-%d')}")
    return ("Unknown Team", "Unknown Team", bet_date.strftime("%Y-%m-%d"))

def search_espn_player(player_name: str, sport: str = "football", league: str = "nfl") -> dict:
    """
    Search for a player on ESPN and return player details
    
    Args:
        player_name: Name of the player to search for
        sport: Sport (default: "football")
        league: League (default: "nfl")
    
    Returns:
        Dictionary with player details or None if not found
    """
    try:
        # ESPN search API
        search_url = f"https://site.api.espn.com/apis/search/v2"
        params = {
            "query": player_name,
            "limit": 10,
            "page": 1,
            "sort": "relevance",
            "active": True,
            "sport": sport,
            "league": league
        }
        
        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Look for player results
        if 'results' in data and len(data['results']) > 0:
            for result in data['results']:
                if result.get('type') == 'player':
                    player_data = result.get('contents', [{}])[0]
                    if player_data:
                        # Extract player ID (integer ID preferred for details API)
                        # UID format: s:40~l:46~a:1966 -> 1966
                        uid = player_data.get('uid', '')
                        player_id = str(player_data.get('id', ''))
                        
                        if 'a:' in uid:
                            try:
                                player_id = uid.split('a:')[-1]
                            except:
                                pass
                        
                        # Fetch full details to get position, jersey, team
                        details = get_espn_player_details(player_id, sport, league)
                        if details:
                            return details

                        # Fallback: Extract what we can from search result
                        position = player_data.get('position', {}).get('abbreviation', '')
                        jersey_number = player_data.get('jersey', '')
                        
                        # Try to parse team from subtitle if team object is empty
                        # Subtitle format: "Los Angeles Lakers"
                        current_team = player_data.get('team', {}).get('displayName', '')
                        if not current_team:
                            current_team = result.get('subtitle', '')
                            
                        # Determine correct sport
                        correct_sport = 'NFL' if league.upper() == 'NFL' else 'NBA' if league.upper() == 'NBA' else sport.upper()
                        
                        player_info = {
                            'espn_player_id': player_id,
                            'player_name': player_data.get('displayName', ''),
                            'position': position if position else None,
                            'jersey_number': jersey_number if jersey_number not in [None, ''] else None,
                            'team_abbreviation': player_data.get('team', {}).get('abbreviation', ''),
                            'current_team': current_team,
                            'sport': correct_sport
                        }
                        return player_info
        
        return None
    except Exception as e:
        print(f"Error searching ESPN for player {player_name}: {e}")
        return None

def _get_player_stats_from_boxscore(player_name: str, sport: str, boxscore: dict) -> dict:
    """
    Extract player stats from boxscore data
    
    Args:
        player_name: Player name to search for
        sport: Sport (NBA or NFL)
        boxscore: Boxscore data from ESPN API
    
    Returns:
        Dictionary with player stats
    """
    if not boxscore:
        return {}
    
    players_data = boxscore.get('players', [])
    combined_stats = {}
    player_found = False
    
    for team_data in players_data:
        statistics = team_data.get('statistics', [])
        for stat_group in statistics:
            group_name = stat_group.get('name', '').lower()
            athletes = stat_group.get('athletes', [])
            
            for athlete in athletes:
                athlete_name = athlete.get('athlete', {}).get('displayName', '')
                # Check for match
                if player_name.lower() in athlete_name.lower() or athlete_name.lower() in player_name.lower():
                    player_found = True
                    stats_list = athlete.get('stats', [])
                    labels = stat_group.get('labels', [])
                    
                    for i, label in enumerate(labels):
                        if i < len(stats_list):
                            try:
                                # Normalize the label key
                                normalized_label = label.lower().strip()
                                stat_value = stats_list[i]
                                
                                # Handle stats that come as ranges (e.g., "1-6" for 3PT)
                                if isinstance(stat_value, str) and '-' in stat_value:
                                    # Parse "made-attempted" format (e.g., "1-6" -> 1)
                                    parts = stat_value.split('-')
                                    if parts[0].isdigit():
                                        stat_value = float(parts[0])  # Take the made number
                                
                                # Convert to float if possible
                                if isinstance(stat_value, str) and stat_value.replace('.', '', 1).isdigit():
                                    stat_value = float(stat_value)
                                elif isinstance(stat_value, (int, float)):
                                    stat_value = float(stat_value)
                                
                                # Store with group prefix (e.g., rushing_yds)
                                prefixed_key = f"{group_name}_{normalized_label}"
                                combined_stats[prefixed_key] = stat_value
                                
                                # Also store without prefix if not exists (for backward compatibility)
                                if normalized_label not in combined_stats:
                                    combined_stats[normalized_label] = stat_value
                                    
                            except (ValueError, TypeError, AttributeError):
                                normalized_label = label.lower().strip()
                                combined_stats[normalized_label] = stats_list[i]
    
    return combined_stats if player_found else {}


def _extract_achieved_value(stats: dict, stat_type: str, bet_type: str, bet_line_type: str) -> float:
    """
    Extract achieved value from player stats based on stat and bet type
    
    Args:
        stats: Player stats dictionary
        stat_type: Type of stat (e.g., 'points', 'assists', 'made_threes')
        bet_type: Type of bet (e.g., 'total', 'made_threes', 'assists')
        bet_line_type: Line type ('over', 'under')
    
    Returns:
        Achieved value or None
    """
    if not stats:
        return None
    
    stat_type_lower = (stat_type or '').lower().strip()
    bet_type_lower = (bet_type or '').lower().strip()
    
    # Helper to check keys
    def check_keys(keys):
        for key in keys:
            if key in stats:
                return stats[key]
        return None

    # --- NFL Mappings ---
    
    # Rushing Yards
    if 'rushing_yards' in stat_type_lower or 'rush_yds' in stat_type_lower:
        val = check_keys(['rushing_yds', 'yds'])
        if val is not None: return val

    # Receiving Yards
    if 'receiving_yards' in stat_type_lower or 'rec_yds' in stat_type_lower:
        val = check_keys(['receiving_yds', 'yds'])
        if val is not None: return val

    # Passing Yards
    if 'passing_yards' in stat_type_lower or 'pass_yds' in stat_type_lower:
        val = check_keys(['passing_yds', 'yds'])
        if val is not None: return val
        
    # Receptions
    if 'receptions' in stat_type_lower or 'catches' in stat_type_lower:
        val = check_keys(['receiving_rec', 'rec'])
        if val is not None: return val
        
    # Touchdowns (Anytime / Total)
    if 'touchdown' in stat_type_lower or 'td' in stat_type_lower:
        # Special case: Passing TDs
        if 'passing' in stat_type_lower or 'pass' in stat_type_lower:
            if 'passing_td' in stats:
                return float(stats['passing_td'])
            return None

        # Sum up all TDs found (excluding passing_td and generic 'td')
        total_td = 0
        found_td = False
        for key, val in stats.items():
            # Skip generic 'td' to avoid double counting
            if key == 'td':
                continue
            
            # Skip 'passing_td' for non-passing TD bets (Anytime TD)
            if key == 'passing_td':
                continue
                
            if key.endswith('_td'):
                try:
                    total_td += float(val)
                    found_td = True
                except:
                    pass
        
        # Fallback: If no specific TDs found but generic 'td' exists, use it
        if not found_td and 'td' in stats:
            try:
                return float(stats['td'])
            except:
                pass
                
        if found_td:
            return total_td

    # --- NBA Mappings ---
    
    if 'point' in stat_type_lower or 'point' in bet_type_lower or 'pts' in stat_type_lower:
        val = check_keys(['pts', 'points'])
        if val is not None: return val
    
    if 'assist' in stat_type_lower or 'ast' in stat_type_lower:
        val = check_keys(['ast', 'assists'])
        if val is not None: return val
    
    if 'rebound' in stat_type_lower or 'reb' in stat_type_lower:
        val = check_keys(['reb', 'rebounds'])
        if val is not None: return val
    
    # Three pointers - ESPN uses "3PT" label
    if 'three' in stat_type_lower or '3p' in stat_type_lower.replace('-', '').replace('_', '') or 'three' in bet_type_lower or '3p' in bet_type_lower.replace('-', '').replace('_', ''):
        # Try ESPN abbreviations first
        val = check_keys(['3pt', '3p', '3-pt'])
        if val is not None:
             if isinstance(val, (int, float)):
                 return val
        
        # Then try full names
        possible_keys = [
            '3-pt made',
            '3-pointers made',
            'three-pointers made',
            'three pointers made',
            'made threes',
            'made 3-pointers',
            'made 3-pt',
        ]
        val = check_keys(possible_keys)
        if val is not None: return val
    
    # Steals
    if 'steal' in stat_type_lower or 'stl' in stat_type_lower:
        val = check_keys(['stl', 'steals'])
        if val is not None: return val
    
    # Blocks
    if 'block' in stat_type_lower or 'blk' in stat_type_lower:
        val = check_keys(['blk', 'blocks'])
        if val is not None: return val
    
    # Turnovers
    if 'turnover' in stat_type_lower or 'to' in stat_type_lower:
        val = check_keys(['to', 'turnovers'])
        if val is not None: return val
    
    # Try direct key match first
    if stat_type_lower in stats:
        return stats[stat_type_lower]
    
    # Check bet_type only if it's not generic 'player prop' or 'team prop'
    if bet_type_lower in stats and bet_type_lower not in ['player prop', 'team prop', 'player_prop', 'team_prop']:
        return stats[bet_type_lower]
    
    # Try removing spaces and special characters
    normalized_stat = stat_type_lower.replace(' ', '').replace('_', '').replace('-', '')
    normalized_bet = bet_type_lower.replace(' ', '').replace('_', '').replace('-', '')
    
    for key in stats.keys():
        normalized_key = key.lower().replace(' ', '').replace('_', '').replace('-', '').replace('.', '')
        if normalized_key == normalized_stat or normalized_key == normalized_bet:
            return stats[key]
    
    return None


def get_espn_game_data(home_team: str, away_team: str, game_date: str, player_name: str = None, sport: str = 'NBA', stat_type: str = None, bet_type: str = None, bet_line_type: str = None, game_id: str = None) -> dict:
    """
    Fetch comprehensive ESPN game data for a specific game
    
    Args:
        home_team: Home team name
        away_team: Away team name  
        game_date: Game date in YYYY-MM-DD format
        player_name: Player name for player props (optional)
        sport: Sport (NBA, NFL, etc.)
        stat_type: Stat type for player props (e.g., 'points', 'assists')
        bet_type: Type of bet (e.g., 'total', 'made_threes')
        bet_line_type: Line type ('over', 'under')
        game_id: Optional ESPN game ID for direct lookup
    
    Returns:
        Dictionary with game data or None if not found
    """
    try:
        # Convert date format
        if not game_date or str(game_date).lower() == 'none':
            return None
            
        date_obj = datetime.strptime(game_date, '%Y-%m-%d')
        espn_date = date_obj.strftime('%Y%m%d')
        
        # Determine sport and league
        if sport and 'NBA' in sport.upper():
            sport_path = "basketball/nba"
        else:
            sport_path = "football/nfl"
        
        url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/scoreboard?dates={espn_date}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        events = data.get('events', [])
        
        for event in events:
            current_game_id = event.get('id')
            
            # Priority 1: Direct Game ID Match
            if game_id and str(game_id) == str(current_game_id):
                # Found exact match by ID - proceed to process this event
                pass
            elif game_id:
                # If game_id was provided but doesn't match this event, skip
                continue
            
            # If no game_id provided, fall back to team matching logic below...
            
            competitions = event.get('competitions', [])
            if not competitions:
                continue
            
            competition = competitions[0]
            competitors = competition.get('competitors', [])
            
            if len(competitors) < 2:
                continue
            
            home_competitor = next((c for c in competitors if c.get('homeAway') == 'home'), None)
            away_competitor = next((c for c in competitors if c.get('homeAway') == 'away'), None)
            
            if not home_competitor or not away_competitor:
                continue
            
            espn_home = home_competitor.get('team', {}).get('displayName', '')
            espn_away = away_competitor.get('team', {}).get('displayName', '')
            
            # Match teams (case-insensitive partial match)
            # Only perform this check if we didn't match by ID
            if not game_id:
                home_match = home_team.lower() in espn_home.lower() or espn_home.lower() in home_team.lower()
                away_match = away_team.lower() in espn_away.lower() or espn_away.lower() in away_team.lower()
                
                if not (home_match and away_match):
                    continue
            
            # Extract data (runs for both ID match and team match)
            home_score = int(home_competitor.get('score', 0))
            away_score = int(away_competitor.get('score', 0))
            
            # Get game status
            game_status_obj = competition.get('status', {})
            # Check for status.type.name (standard structure) or status.name (fallback)
            game_status_name = game_status_obj.get('type', {}).get('name') or game_status_obj.get('name', 'STATUS_END_PERIOD')
            
            achieved_value = None
            is_home_game = None
            
            if player_name:
                # Fetch detailed boxscore for player stats
                try:
                    summary_url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/summary?event={current_game_id}"
                    summary_response = requests.get(summary_url, headers=headers, timeout=10)
                    if summary_response.status_code == 200:
                        summary_data = summary_response.json()
                        boxscore = summary_data.get('boxscore', {})
                        
                        # Get player stats from boxscore
                        player_stats = _get_player_stats_from_boxscore(player_name, sport, boxscore)
                        
                        if player_stats:
                            # Extract the relevant stat
                            achieved_value = _extract_achieved_value(player_stats, stat_type, bet_type, bet_line_type)
                except Exception as e:
                    print(f"Error fetching player stats for {player_name}: {e}")
            
            return {
                'game_id': current_game_id,
                'home_score': home_score,
                'away_score': away_score,
                'is_home_game': is_home_game,
                'achieved_value': achieved_value,
                'game_status': game_status_name
            }
        
        return None
        
    except Exception as e:
        print(f"Error fetching ESPN game data: {e}")
        return None

def get_espn_player_details(player_id: str, sport: str = "football", league: str = "nfl") -> dict:
    """
    Get detailed player information from ESPN
    
    Args:
        player_id: ESPN player ID
        sport: Sport (default: "football")
        league: League (default: "nfl")
    
    Returns:
        Dictionary with detailed player information
    """
    try:
        # ESPN player details API
        url = f"https://site.web.api.espn.com/apis/common/v3/sports/{sport}/{league}/athletes/{player_id}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'athlete' in data:
            athlete = data['athlete']
            team = athlete.get('team', {})
            
            position = athlete.get('position', {}).get('abbreviation', '')
            jersey_number = athlete.get('jersey', '')
            
            # Determine correct sport
            correct_sport = 'NFL' if league.upper() == 'NFL' else 'NBA' if league.upper() == 'NBA' else sport.upper()
            
            player_info = {
                'espn_player_id': str(athlete.get('id', '')),
                'player_name': athlete.get('displayName', ''),
                'position': position if position else None,
                'jersey_number': jersey_number if jersey_number not in [None, ''] else None,
                'team_abbreviation': team.get('abbreviation', ''),
                'current_team': team.get('displayName', ''),
                'status': athlete.get('status', {}).get('type', ''),
                'sport': correct_sport
            }
            return player_info
        
        return None
    except Exception as e:
        print(f"Error fetching ESPN player details for ID {player_id}: {e}")
        return None

# Stats Standardization Mapping
STATS_MAPPING = {
    "nba": {
        "points": "points",
        "totalRebounds": "rebounds",
        "assists": "assists",
        "steals": "steals",
        "blocks": "blocks",
        "turnovers": "turnovers",
        "fieldGoalsMade": "field_goals_made",
        "fieldGoalsAttempted": "field_goals_attempted",
        "threePointFieldGoalsMade": "three_pointers_made",
        "threePointFieldGoalsAttempted": "three_pointers_attempted",
        "freeThrowsMade": "free_throws_made",
        "freeThrowsAttempted": "free_throws_attempted",
        "fieldGoalPct": "field_goal_pct",
        "threePointFieldGoalPct": "three_point_pct",
        "freeThrowPct": "free_throw_pct",
        "gamesPlayed": "games_played",
        "minutes": "minutes",
        "plusMinus": "plus_minus",
        "PTS": "points",
        "REB": "rebounds",
        "AST": "assists",
        "STL": "steals",
        "BLK": "blocks",
        "TO": "turnovers",
        "MIN": "minutes",
        "+/-": "plus_minus",
        "FG": "field_goals", # usually split later
        "3PT": "three_pointers",
        "FT": "free_throws",
        "PF": "fouls"
    },
    "nfl": {
        "passingYards": "passing_yards",
        "rushingYards": "rushing_yards",
        "receivingYards": "receiving_yards",
        "passingTouchdowns": "passing_touchdowns",
        "rushingTouchdowns": "rushing_touchdowns",
        "receivingTouchdowns": "receiving_touchdowns",
        "totalTouchdowns": "total_touchdowns",
        "interceptions": "interceptions",
        "sacks": "sacks",
        "fumbles": "fumbles",
        "completions": "completions",
        "attempts": "attempts",
        "receptions": "receptions",
        "targets": "targets",
        "gamesPlayed": "games_played"
    },
    "mlb": {
        "avg": "batting_average",
        "homeRuns": "home_runs",
        "RBIs": "rbi",
        "runs": "runs",
        "hits": "hits",
        "stolenBases": "stolen_bases",
        "OPS": "ops",
        "ERA": "era",
        "wins": "wins",
        "losses": "losses",
        "strikeouts": "strikeouts",
        "saves": "saves",
        "gamesPlayed": "games_played"
    },
    "nhl": {
        "goals": "goals",
        "assists": "assists",
        "points": "points",
        "plusMinus": "plus_minus",
        "timeOnIce": "time_on_ice",
        "powerPlayGoals": "power_play_goals",
        "powerPlayAssists": "power_play_assists",
        "shots": "shots",
        "saves": "saves",
        "savePct": "save_pct",
        "goalsAgainstAverage": "goals_against_average",
        "shutouts": "shutouts",
        "gamesPlayed": "games_played"
    }
}

def standardize_keys(stats_dict, league):
    """Standardize keys based on league mapping"""
    if not stats_dict or not league:
        return stats_dict
        
    mapping = STATS_MAPPING.get(league.lower(), {})
    standardized = {}
    
    for k, v in stats_dict.items():
        # Check if key is in mapping
        new_key = mapping.get(k, k) # Default to original if not found
        
        # Handle special cases like "FG" -> "3-10"
        if league.lower() == 'nba' and k in ['FG', '3PT', 'FT'] and isinstance(v, str) and '-' in v:
            try:
                made, att = v.split('-')
                prefix = "field_goals" if k == 'FG' else "three_pointers" if k == '3PT' else "free_throws"
                standardized[f"{prefix}_made"] = int(made)
                standardized[f"{prefix}_attempted"] = int(att)
                # Calculate pct if possible
                if int(att) > 0:
                    standardized[f"{prefix}_pct"] = round((int(made) / int(att)) * 100, 1)
            except:
                standardized[new_key] = v
        else:
            standardized[new_key] = v
            
    return standardized

def get_player_season_stats(player_id: str, sport: str = "football", league: str = "nfl") -> dict:
    """
    Get comprehensive player season stats from ESPN
    
    Args:
        player_id: ESPN player ID
        sport: Sport (default: "football")
        league: League (default: "nfl")
    
    Returns:
        Dictionary with:
        - stats_season: Season averages/totals + season_year
        - stats_last_5_games: List of last 5 game logs
    """
    try:
        stats_season = {}
        stats_last_5_games = []
        season_year = None
        
        # 1. Fetch Detailed Stats (Averages & Totals)
        # Use the /stats endpoint for better granularity
        stats_url = f"https://site.web.api.espn.com/apis/common/v3/sports/{sport}/{league}/athletes/{player_id}/stats"
        
        try:
            response = requests.get(stats_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # Process categories (Regular Season Averages, Totals, etc.)
                if 'categories' in data:
                    for cat in data['categories']:
                        cat_name = cat.get('name')
                        names = cat.get('names', [])
                        
                        # Look for Regular Season stats
                        if 'statistics' in cat:
                            # Find the latest season dynamically
                            latest_stat = None
                            max_year = 0
                            
                            for stat in cat['statistics']:
                                season = stat.get('season', {})
                                year = season.get('year', 0)
                                if year > max_year:
                                    max_year = year
                                    latest_stat = stat
                            
                            if latest_stat:
                                # Capture the season year
                                if not season_year:
                                    season_year = latest_stat.get('season', {}).get('displayName')
                                
                                values = latest_stat.get('stats', [])
                                
                                if len(names) == len(values):
                                        for k, v in zip(names, values):
                                            # Clean and convert values
                                            try:
                                                # Handle combined keys (e.g. "avgThreePointFieldGoalsMade-avgThreePointFieldGoalsAttempted")
                                                if '-' in k and isinstance(v, str) and '-' in v:
                                                    k_parts = k.split('-')
                                                    v_parts = v.split('-')
                                                    
                                                    if len(k_parts) == len(v_parts):
                                                        for sub_k, sub_v in zip(k_parts, v_parts):
                                                            try:
                                                                if '.' in sub_v:
                                                                    stats_season[sub_k] = float(sub_v)
                                                                else:
                                                                    stats_season[sub_k] = int(sub_v.replace(',', ''))
                                                            except:
                                                                stats_season[sub_k] = sub_v
                                                        continue # Skip the main assignment

                                                if isinstance(v, str):
                                                    if '.' in v:
                                                        val = float(v)
                                                    else:
                                                        val = int(v.replace(',', ''))
                                                else:
                                                    val = v
                                                
                                                stats_season[k] = val
                                            except:
                                                stats_season[k] = v
        except Exception as e:
            print(f"Error fetching detailed stats: {e}")

        # Add season year to stats
        if season_year:
            stats_season['season_year'] = season_year

        # 2. Fallback/Supplement with Overview (if detailed failed or missing basics)
        if not stats_season:
            url = f"https://site.web.api.espn.com/apis/common/v3/sports/{sport}/{league}/athletes/{player_id}/overview"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'statistics' in data:
                    stats_data = data['statistics']
                    keys = stats_data.get('names', [])
                    splits = stats_data.get('splits', [])
                    for split in splits:
                        if split.get('displayName') == 'Regular Season':
                            values = split.get('stats', [])
                            if len(keys) == len(values):
                                for k, v in zip(keys, values):
                                    try:
                                        if '.' in v:
                                            stats_season[k] = float(v)
                                        else:
                                            stats_season[k] = int(v.replace(',', ''))
                                    except:
                                        stats_season[k] = v
                            break

        # 3. Calculate True Shooting Percentage (TS%) for NBA
        # Formula: PTS / (2 * (FGA + 0.44 * FTA))
        if league.lower() == 'nba':
            try:
                pts = float(stats_season.get('points', 0))
                
                # Need totals for FGA and FTA
                # If we only have averages, the formula still works mathematically for the rate
                # But typically TS% is calculated on totals. Let's try to find totals keys.
                # From research: 'fieldGoalsMade-fieldGoalsAttempted' might be the key for totals
                
                fga = 0
                fta = 0
                
                # Try to find FGA
                if 'fieldGoalsAttempted' in stats_season:
                    fga = float(stats_season['fieldGoalsAttempted'])
                elif 'avgFieldGoalsAttempted' in stats_season:
                     fga = float(stats_season['avgFieldGoalsAttempted'])

                # Try to find FTA
                if 'freeThrowsAttempted' in stats_season:
                    fta = float(stats_season['freeThrowsAttempted'])
                elif 'avgFreeThrowsAttempted' in stats_season:
                    fta = float(stats_season['avgFreeThrowsAttempted'])
                
                if pts > 0 and (fga + 0.44 * fta) > 0:
                    ts_pct = pts / (2 * (fga + 0.44 * fta))
                    stats_season['trueShootingPct'] = round(ts_pct * 100, 1) # Store as percentage (e.g. 58.5)
                    
            except Exception as e:
                print(f"Error calculating TS%: {e}")

        # 4. Fetch Last 5 Games Log
        try:
            log_url = f"https://site.web.api.espn.com/apis/common/v3/sports/{sport}/{league}/athletes/{player_id}/gamelog"
            # print(f"Fetching game log from: {log_url}")
            log_response = requests.get(log_url, timeout=10)
            
            if log_response.status_code == 200:
                log_data = log_response.json()
                
                # Get labels mapping
                log_names = log_data.get('names', [])
                # print(f"Log names: {log_names}")
                
                if 'events' in log_data:
                    events = log_data['events']
                    # print(f"Events type: {type(events)}")
                    
                    if isinstance(events, dict):
                         # Handle case where events is a dict (seen in research)
                         events = list(events.values())
                    
                    
                    # Ensure events is a list before slicing
                    if isinstance(events, list):
                        # Take up to 5
                        for event in events[:5]:
                            game_stats = {}
                            game_id = event.get('id')
                            
                            # Basic info
                            game_stats['gameId'] = game_id
                            game_stats['gameDate'] = event.get('gameDate')
                            game_stats['opponent'] = event.get('opponent', {}).get('abbreviation')
                            
                            # Fetch detailed boxscore for this game
                            try:
                                summary_url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/summary?event={game_id}"
                                summary_res = requests.get(summary_url, timeout=5)
                                if summary_res.status_code == 200:
                                    summary_data = summary_res.json()
                                    if 'boxscore' in summary_data and 'players' in summary_data['boxscore']:
                                        # Find player in boxscore
                                        found_stats = False
                                        for team_box in summary_data['boxscore']['players']:
                                            if 'statistics' in team_box:
                                                stats_wrapper = team_box['statistics'][0]
                                                names = stats_wrapper.get('names', [])
                                                athletes = stats_wrapper.get('athletes', [])
                                                
                                                for athlete in athletes:
                                                    if athlete.get('athlete', {}).get('id') == player_id:
                                                        stats_vals = athlete.get('stats', [])
                                                        if len(names) == len(stats_vals):
                                                            for k, v in zip(names, stats_vals):
                                                                game_stats[k] = v
                                                        found_stats = True
                                                        break
                                            if found_stats:
                                                break
                            except Exception as e:
                                print(f"Error fetching boxscore for game {game_id}: {e}")
                            
                            # Standardize game stats immediately
                            game_stats = standardize_keys(game_stats, league)
                            stats_last_5_games.append(game_stats)
                    else:
                        print(f"Events is not a list: {type(events)}")
                    
        except Exception as e:
            print(f"Error fetching game log: {e}")
        
        # Standardize season stats
        stats_season = standardize_keys(stats_season, league)
        
        # Wrap in season year structure
        final_season_stats = {}
        if season_year:
            # Ensure season_year is in the stats object too
            stats_season['season_year'] = season_year
            final_season_stats[season_year] = stats_season
        else:
            # Fallback if no year found
            final_season_stats['current'] = stats_season
        
        return {
            'stats_season': final_season_stats,
            'stats_last_5_games': stats_last_5_games
        }
        
    except Exception as e:
        print(f"Error fetching ESPN player stats for ID {player_id}: {e}")
        return None
