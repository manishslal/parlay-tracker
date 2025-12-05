
import requests
import time
from datetime import datetime
import logging
from app import app, db
from models import Team

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ESPN API endpoints
SPORTS_CONFIG = {
    'NFL': {
        'url': "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams",
        'sport_key': 'football',
        'league_key': 'nfl'
    },
    'NBA': {
        'url': "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams",
        'sport_key': 'basketball',
        'league_key': 'nba'
    },
    'MLB': {
        'url': "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams",
        'sport_key': 'baseball',
        'league_key': 'mlb'
    },
    'NHL': {
        'url': "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams",
        'sport_key': 'hockey',
        'league_key': 'nhl'
    }
}

def fetch_espn_data(url, description):
    """Fetch data from ESPN API with error handling."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        logger.info(f"Fetching {description}...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        time.sleep(0.5)  # Rate limiting
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch {description}: {e}")
        return None

def extract_team_info(team_data, sport):
    """Extract team information from ESPN team data."""
    team = team_data.get('team', {})
    
    # Basic info
    team_info = {
        'team_name': team.get('displayName', ''),
        'team_name_short': team.get('shortDisplayName', ''),
        'team_abbr': team.get('abbreviation', ''),
        'espn_team_id': team.get('id', ''),
        'sport': sport,
        'location': team.get('location', ''),
        'nickname': team.get('name', ''),
        'is_active': True
    }
    
    # Logos
    logos = team.get('logos', [])
    if logos:
        team_info['logo_url'] = logos[0].get('href', '')
    
    # Colors
    team_info['color'] = team.get('color', '')
    team_info['alternate_color'] = team.get('alternateColor', '')
    
    # Record
    record = team.get('record', {})
    if record:
        items = record.get('items', [])
        for item in items:
            if item.get('type') == 'total':
                stats = item.get('stats', [])
                for stat in stats:
                    stat_name = stat.get('name')
                    stat_value = stat.get('value')
                    
                    if stat_name == 'gamesPlayed':
                        team_info['games_played'] = int(stat_value)
                    elif stat_name == 'wins':
                        team_info['wins'] = int(stat_value)
                    elif stat_name == 'losses':
                        team_info['losses'] = int(stat_value)
                    elif stat_name == 'ties':
                        team_info['ties'] = int(stat_value)
                    elif stat_name == 'winPercent':
                        team_info['win_percentage'] = float(stat_value)
    
    # Standings
    standings = team.get('standingSummary', '')
    if standings:
        # Extract division/conference rank if available
        parts = standings.split(',')
        for part in parts:
            part = part.strip().lower()
            if 'in division' in part or 'in conference' in part:
                try:
                    rank_str = part.split()[0].replace('st', '').replace('nd', '').replace('rd', '').replace('th', '')
                    if rank_str.isdigit():
                        rank = int(rank_str)
                        if 'division' in part:
                            team_info['division_rank'] = rank
                        elif 'conference' in part:
                            team_info['conference_rank'] = rank
                except:
                    pass
    
    # League/Conference/Division
    groups = team.get('groups', {})
    if groups:
        team_info['league'] = groups.get('name', '')
        parent = groups.get('parent', {})
        if parent:
            team_info['conference'] = parent.get('name', '')
            grandparent = parent.get('parent', {})
            if grandparent:
                team_info['division'] = grandparent.get('name', '')
    
    # Next event
    next_event = team.get('nextEvent', [])
    if next_event and len(next_event) > 0:
        event_date = next_event[0].get('date')
        if event_date:
            try:
                # Handle ISO format with Z
                team_info['next_game_date'] = datetime.fromisoformat(event_date.replace('Z', '+00:00')).date()
            except:
                pass
    
    return team_info

def update_teams_for_sport(sport, config):
    """Update teams for a specific sport."""
    logger.info(f"Updating {sport} teams...")
    
    data = fetch_espn_data(config['url'], f"{sport} teams")
    if not data:
        return 0, 0
    
    sports_data = data.get('sports', [])
    if not sports_data:
        logger.warning(f"No sports data found for {sport}")
        return 0, 0
    
    leagues = sports_data[0].get('leagues', [])
    if not leagues:
        logger.warning(f"No leagues found for {sport}")
        return 0, 0
    
    all_teams = leagues[0].get('teams', [])
    logger.info(f"Found {len(all_teams)} teams for {sport}")
    
    updated_count = 0
    created_count = 0
    
    for team_data in all_teams:
        try:
            info = extract_team_info(team_data, sport)
            
            if not info.get('team_name') or not info.get('team_abbr'):
                continue
                
            # Find existing team
            team = Team.query.filter_by(espn_team_id=info['espn_team_id'], sport=sport).first()
            
            if not team:
                # Try by abbreviation if ID not found
                team = Team.query.filter_by(team_abbr=info['team_abbr'], sport=sport).first()
            
            if team:
                # Update existing
                team.team_name = info['team_name']
                team.team_name_short = info['team_name_short']
                team.team_abbr = info['team_abbr']
                
                # Only update espn_team_id if it's different and doesn't conflict
                if team.espn_team_id != info['espn_team_id']:
                    # Check for conflict GLOBALLY (since unique=True in model)
                    conflict = Team.query.filter_by(espn_team_id=info['espn_team_id']).first()
                    if not conflict:
                        team.espn_team_id = info['espn_team_id']
                    else:
                        logger.warning(f"Skipping ID update for {team.team_name}: ID {info['espn_team_id']} already used by {conflict.team_name} ({conflict.sport})")

                team.location = info['location']
                team.nickname = info['nickname']
                
                if info.get('logo_url'):
                    team.logo_url = info['logo_url']
                if info.get('color'):
                    team.color = info['color']
                if info.get('alternate_color'):
                    team.alternate_color = info['alternate_color']
                
                # Stats
                team.games_played = info.get('games_played', team.games_played)
                team.wins = info.get('wins', team.wins)
                team.losses = info.get('losses', team.losses)
                team.ties = info.get('ties', team.ties)
                team.win_percentage = info.get('win_percentage', team.win_percentage)
                team.division_rank = info.get('division_rank', team.division_rank)
                team.conference_rank = info.get('conference_rank', team.conference_rank)
                
                # Structure
                if info.get('league'): team.league = info['league']
                if info.get('conference'): team.conference = info['conference']
                if info.get('division'): team.division = info['division']
                
                if info.get('next_game_date'):
                    team.next_game_date = info['next_game_date']
                
                team.last_stats_update = datetime.utcnow()
                team.updated_at = datetime.utcnow()
                
                updated_count += 1
            else:
                # Create new
                # Check for ID conflict first
                conflict = Team.query.filter_by(espn_team_id=info['espn_team_id']).first()
                if conflict:
                    logger.warning(f"Skipping creation of {info['team_name']} ({sport}): ID {info['espn_team_id']} already used by {conflict.team_name} ({conflict.sport})")
                    continue

                team = Team(
                    team_name=info['team_name'],
                    team_name_short=info['team_name_short'],
                    team_abbr=info['team_abbr'],
                    espn_team_id=info['espn_team_id'],
                    sport=sport,
                    league=info.get('league'),
                    conference=info.get('conference'),
                    division=info.get('division'),
                    location=info['location'],
                    nickname=info['nickname'],
                    logo_url=info.get('logo_url'),
                    color=info.get('color'),
                    alternate_color=info.get('alternate_color'),
                    games_played=info.get('games_played', 0),
                    wins=info.get('wins', 0),
                    losses=info.get('losses', 0),
                    ties=info.get('ties', 0),
                    win_percentage=info.get('win_percentage'),
                    division_rank=info.get('division_rank'),
                    conference_rank=info.get('conference_rank'),
                    next_game_date=info.get('next_game_date'),
                    last_stats_update=datetime.utcnow(),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    is_active=True
                )
                db.session.add(team)
                created_count += 1
                
        except Exception as e:
            logger.error(f"Error processing team {info.get('team_name', 'Unknown')}: {e}")
            continue
            
    return updated_count, created_count

def update_teams():
    """Main function to update all teams."""
    logger.info("Starting team data update...")
    
    with app.app_context():
        total_updated = 0
        total_created = 0
        
        for sport, config in SPORTS_CONFIG.items():
            updated, created = update_teams_for_sport(sport, config)
            total_updated += updated
            total_created += created
            logger.info(f"{sport}: Updated {updated}, Created {created}")
        
        try:
            db.session.commit()
            logger.info(f"Team update complete. Total Updated: {total_updated}, Total Created: {total_created}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to commit team updates: {e}")

if __name__ == "__main__":
    update_teams()
