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

def get_espn_games_with_ids_for_date(date: datetime) -> List[Tuple[str, str, str]]:
    """
    Fetch games from ESPN API for a given date (NFL and NBA)
    Returns list of (game_id, away_team, home_team) tuples
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
                                games.append((game_id, away_team, home_team))
        
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
                        # Extract player information
                        position = player_data.get('position', {}).get('abbreviation', '')
                        jersey_number = player_data.get('jersey', '')
                        
                        # Determine correct sport
                        correct_sport = 'NFL' if league.upper() == 'NFL' else 'NBA' if league.upper() == 'NBA' else sport.upper()
                        
                        player_info = {
                            'espn_player_id': str(player_data.get('id', '')),
                            'player_name': player_data.get('displayName', ''),
                            'position': position if position else None,
                            'jersey_number': jersey_number if jersey_number not in [None, ''] else None,
                            'team_abbreviation': player_data.get('team', {}).get('abbreviation', ''),
                            'current_team': player_data.get('team', {}).get('displayName', ''),
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
    
    for team_data in players_data:
        statistics = team_data.get('statistics', [])
        for stat_group in statistics:
            athletes = stat_group.get('athletes', [])
            for athlete in athletes:
                athlete_name = athlete.get('athlete', {}).get('displayName', '')
                if player_name.lower() in athlete_name.lower() or athlete_name.lower() in player_name.lower():
                    # Found the player, extract stats
                    stats_list = athlete.get('stats', [])
                    labels = stat_group.get('labels', [])
                    
                    stats_dict = {}
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
                                
                                stats_dict[normalized_label] = stat_value
                            except (ValueError, TypeError, AttributeError):
                                normalized_label = label.lower().strip()
                                stats_dict[normalized_label] = stats_list[i]
                    
                    return stats_dict
    
    return {}


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
    
    # NBA stat mappings - ordered by specificity
    # ESPN uses abbreviations: PTS, AST, REB, 3PT, STL, BLK, TO
    
    if 'point' in stat_type_lower or 'point' in bet_type_lower or 'pts' in stat_type_lower:
        for key in ['pts', 'points']:
            if key in stats:
                return stats[key]
    
    if 'assist' in stat_type_lower or 'ast' in stat_type_lower:
        for key in ['ast', 'assists']:
            if key in stats:
                return stats[key]
    
    if 'rebound' in stat_type_lower or 'reb' in stat_type_lower:
        for key in ['reb', 'rebounds']:
            if key in stats:
                return stats[key]
    
    # Three pointers - ESPN uses "3PT" label
    if 'three' in stat_type_lower or '3p' in stat_type_lower.replace('-', '').replace('_', '') or 'three' in bet_type_lower or '3p' in bet_type_lower.replace('-', '').replace('_', ''):
        # Try ESPN abbreviations first
        for key in ['3pt', '3p', '3-pt']:
            if key in stats:
                val = stats[key]
                # If it's a float already, return it
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
        for key in possible_keys:
            if key in stats:
                return stats[key]
    
    # Steals
    if 'steal' in stat_type_lower or 'stl' in stat_type_lower:
        for key in ['stl', 'steals']:
            if key in stats:
                return stats[key]
    
    # Blocks
    if 'block' in stat_type_lower or 'blk' in stat_type_lower:
        for key in ['blk', 'blocks']:
            if key in stats:
                return stats[key]
    
    # Turnovers
    if 'turnover' in stat_type_lower or 'to' in stat_type_lower:
        for key in ['to', 'turnovers']:
            if key in stats:
                return stats[key]
    
    # Try direct key match first
    if stat_type_lower in stats:
        return stats[stat_type_lower]
    
    if bet_type_lower in stats:
        return stats[bet_type_lower]
    
    # Try removing spaces and special characters
    normalized_stat = stat_type_lower.replace(' ', '').replace('_', '').replace('-', '')
    normalized_bet = bet_type_lower.replace(' ', '').replace('_', '').replace('-', '')
    
    for key in stats.keys():
        normalized_key = key.lower().replace(' ', '').replace('_', '').replace('-', '').replace('.', '')
        if normalized_key == normalized_stat or normalized_key == normalized_bet:
            return stats[key]
    
    return None


def get_espn_game_data(home_team: str, away_team: str, game_date: str, player_name: str = None, sport: str = 'NBA', stat_type: str = None, bet_type: str = None, bet_line_type: str = None) -> dict:
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
    
    Returns:
        Dictionary with game data or None if not found
    """
    try:
        # Convert date format
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
            game_id = event.get('id')
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
            home_match = home_team.lower() in espn_home.lower() or espn_home.lower() in home_team.lower()
            away_match = away_team.lower() in espn_away.lower() or espn_away.lower() in away_team.lower()
            
            if home_match and away_match:
                home_score = int(home_competitor.get('score', 0))
                away_score = int(away_competitor.get('score', 0))
                
                # Get game status
                game_status_obj = competition.get('status', {})
                game_status_name = game_status_obj.get('name', 'STATUS_END_PERIOD')
                
                achieved_value = None
                is_home_game = None
                
                if player_name:
                    # Fetch detailed boxscore for player stats
                    try:
                        summary_url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/summary?event={game_id}"
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
                    'game_id': game_id,
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
        url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/athletes/{player_id}"
        
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
                'sport': correct_sport
            }
            return player_info
        
        return None
    except Exception as e:
        print(f"Error fetching ESPN player details for ID {player_id}: {e}")
        return None
