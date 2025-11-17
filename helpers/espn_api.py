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
    Fetch NFL games from ESPN API for a given date
    Returns list of (game_id, away_team, home_team) tuples
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
        
        return games
    except Exception as e:
        print(f"Error fetching ESPN data for {date_str}: {e}")
        return []

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
                        player_info = {
                            'espn_player_id': str(player_data.get('id', '')),
                            'player_name': player_data.get('displayName', ''),
                            'position': player_data.get('position', {}).get('abbreviation', ''),
                            'jersey_number': player_data.get('jersey', ''),
                            'team_abbreviation': player_data.get('team', {}).get('abbreviation', ''),
                            'current_team': player_data.get('team', {}).get('displayName', ''),
                            'sport': sport.upper()
                        }
                        return player_info
        
        return None
    except Exception as e:
        print(f"Error searching ESPN for player {player_name}: {e}")
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
            
            player_info = {
                'espn_player_id': str(athlete.get('id', '')),
                'player_name': athlete.get('displayName', ''),
                'position': athlete.get('position', {}).get('abbreviation', ''),
                'jersey_number': athlete.get('jersey', ''),
                'team_abbreviation': team.get('abbreviation', ''),
                'current_team': team.get('displayName', ''),
                'sport': sport.upper()
            }
            return player_info
        
        return None
    except Exception as e:
        print(f"Error fetching ESPN player details for ID {player_id}: {e}")
        return None
