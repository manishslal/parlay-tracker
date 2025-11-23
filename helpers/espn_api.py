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
                            'jersey_number': jersey_number if jersey_number else None,
                            'team_abbreviation': player_data.get('team', {}).get('abbreviation', ''),
                            'current_team': player_data.get('team', {}).get('displayName', ''),
                            'sport': correct_sport
                        }
                        return player_info
        
        return None
    except Exception as e:
        print(f"Error searching ESPN for player {player_name}: {e}")
        return None

def get_espn_game_data(home_team: str, away_team: str, game_date: str, player_name: str = None) -> dict:
    """
    Fetch comprehensive ESPN game data for a specific game
    
    Args:
        home_team: Home team name
        away_team: Away team name  
        game_date: Game date in YYYY-MM-DD format
        player_name: Player name for player props (optional)
    
    Returns:
        Dictionary with game data or None if not found
    """
    try:
        # Convert date format
        date_obj = datetime.strptime(game_date, '%Y-%m-%d')
        espn_date = date_obj.strftime('%Y%m%d')
        
        url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={espn_date}"
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
                
                # Determine if player is home or away (simplified - would need better player team lookup)
                is_home_game = None
                achieved_value = None
                
                if player_name:
                    # For now, return None for player stats - would need player stats API integration
                    # This is a placeholder for future player stats fetching
                    achieved_value = None
                    is_home_game = None
                else:
                    # For team bets, determine home/away based on team names
                    is_home_game = None  # Not applicable for team bets
                
                return {
                    'game_id': game_id,
                    'home_score': home_score,
                    'away_score': away_score,
                    'is_home_game': is_home_game,
                    'achieved_value': achieved_value
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
                'jersey_number': jersey_number if jersey_number else None,
                'team_abbreviation': team.get('abbreviation', ''),
                'current_team': team.get('displayName', ''),
                'sport': correct_sport
            }
            return player_info
        
        return None
    except Exception as e:
        print(f"Error fetching ESPN player details for ID {player_id}: {e}")
        return None
