#!/usr/bin/env python3
"""
Enhanced script to populate missing player data with fallback strategies
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from database import db
from models import Player
from helpers.espn_api import search_espn_player, get_espn_player_details
from datetime import datetime
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def search_espn_by_last_name(last_name: str, sport: str = "football", league: str = "nfl") -> list:
    """
    Search ESPN by last name only to find potential matches
    """
    try:
        search_url = "https://site.api.espn.com/apis/search/v2"
        params = {
            "query": last_name,
            "limit": 20,  # Get more results for last name searches
            "page": 1,
            "sort": "relevance",
            "active": True,
            "sport": sport,
            "league": league
        }

        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        players = []
        if 'results' in data and len(data['results']) > 0:
            for result in data['results']:
                if result.get('type') == 'player':
                    player_data = result.get('contents', [{}])[0]
                    if player_data:
                        player_info = {
                            'espn_player_id': str(player_data.get('id', '')),
                            'player_name': player_data.get('displayName', ''),
                            'position': player_data.get('position', {}).get('abbreviation', ''),
                            'jersey_number': player_data.get('jersey', ''),
                            'team_abbreviation': player_data.get('team', {}).get('abbreviation', ''),
                            'current_team': player_data.get('team', {}).get('displayName', ''),
                            'sport': sport.upper()
                        }
                        players.append(player_info)

        return players
    except Exception as e:
        print(f"Error searching ESPN by last name {last_name}: {e}")
        return []

def get_current_team_roster(team_abbr: str, sport: str = "football", league: str = "nfl") -> list:
    """
    Get current roster for a team to help with player matching
    """
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/teams/{team_abbr}/roster"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        players = []
        if 'athletes' in data:
            for athlete in data['athletes']:
                player_info = {
                    'espn_player_id': str(athlete.get('id', '')),
                    'player_name': athlete.get('displayName', ''),
                    'position': athlete.get('position', {}).get('abbreviation', ''),
                    'jersey_number': athlete.get('jersey', ''),
                    'status': athlete.get('status', {}).get('name', 'active')
                }
                players.append(player_info)

        return players
    except Exception as e:
        print(f"Error getting roster for {team_abbr}: {e}")
        return []

def match_player_with_fallbacks(player_name: str, known_team: str = None) -> dict:
    """
    Try multiple strategies to find player data
    """
    print(f"Searching for player: {player_name}")

    # Strategy 1: Full name search
    player_data = search_espn_player(player_name, sport="football", league="nfl")
    if player_data:
        print(f"  ✓ Found by full name: {player_data['player_name']}")
        return player_data

    # Strategy 2: Last name search
    name_parts = player_name.split()
    if len(name_parts) >= 2:
        last_name = name_parts[-1]
        print(f"  Trying last name search: {last_name}")

        candidates = search_espn_by_last_name(last_name)

        # Filter by first name initial
        first_initial = name_parts[0][0].upper()
        matching_candidates = []

        for candidate in candidates:
            candidate_name_parts = candidate['player_name'].split()
            if candidate_name_parts and candidate_name_parts[0][0].upper() == first_initial:
                matching_candidates.append(candidate)

        if matching_candidates:
            # If we have a known team, prefer that
            if known_team:
                for candidate in matching_candidates:
                    if candidate.get('current_team') and known_team.lower() in candidate['current_team'].lower():
                        print(f"  ✓ Found by last name + team match: {candidate['player_name']} ({candidate['current_team']})")
                        return candidate

            # Otherwise take the first match
            candidate = matching_candidates[0]
            print(f"  ✓ Found by last name + initial match: {candidate['player_name']}")
            return candidate

    # Strategy 3: If we know the team, search team roster
    if known_team:
        # Try to get team abbreviation
        team_abbr_map = {
            'houston texans': 'hou',
            'houston': 'hou',
            'texans': 'hou',
            'hou': 'hou'
        }

        team_abbr = None
        for key, abbr in team_abbr_map.items():
            if key in known_team.lower():
                team_abbr = abbr
                break

        if team_abbr:
            print(f"  Trying team roster search: {team_abbr}")
            roster = get_current_team_roster(team_abbr)

            # Look for name matches in roster
            for roster_player in roster:
                if player_name.lower() in roster_player['player_name'].lower() or \
                   roster_player['player_name'].lower() in player_name.lower():
                    print(f"  ✓ Found in team roster: {roster_player['player_name']}")
                    # Get detailed data for this player
                    detailed_data = get_espn_player_details(roster_player['espn_player_id'])
                    if detailed_data:
                        return detailed_data

    print(f"  ✗ No matches found for {player_name}")
    return None

def update_missing_player_data():
    with app.app_context():
        print("Updating missing player data with enhanced fallback strategies...")

        # Focus on players with ESPN IDs but missing key data
        players_to_update = Player.query.filter(
            Player.espn_player_id.isnot(None),
            db.or_(
                Player.position.is_(None),
                Player.current_team.is_(None)
            )
        ).all()

        print(f"Found {len(players_to_update)} players to update")

        updated_count = 0

        for player in players_to_update:
            print(f"\nUpdating {player.player_name} (ID: {player.id})")

            # Try to get detailed data using current ESPN ID
            detailed_data = get_espn_player_details(player.espn_player_id, sport="football", league="nfl")

            if detailed_data:
                print(f"  ✓ Got detailed data from ESPN")
                updated = update_player_from_data(player, detailed_data)
                if updated:
                    updated_count += 1
            else:
                print(f"  ✗ Detailed API failed, trying fallback search")

                # Try fallback search with known information
                fallback_data = match_player_with_fallbacks(player.player_name)

                if fallback_data:
                    # Update ESPN ID if we found a better match
                    if fallback_data['espn_player_id'] != player.espn_player_id:
                        print(f"  Updated ESPN ID: {player.espn_player_id} -> {fallback_data['espn_player_id']}")
                        player.espn_player_id = fallback_data['espn_player_id']

                    updated = update_player_from_data(player, fallback_data)
                    if updated:
                        updated_count += 1

        # Special handling for Nico Collins with known team info
        nico = Player.query.filter_by(player_name='Nico Collins').first()
        if nico and (not nico.position or not nico.current_team):
            print(f"\nSpecial handling for Nico Collins (known: WR, Houston Texans)")

            # Manually set the known data
            if not nico.position:
                nico.position = 'WR'
                print(f"  ✓ Set position to WR")

            if not nico.current_team:
                nico.current_team = 'Houston Texans'
                nico.team_abbreviation = 'HOU'
                print(f"  ✓ Set team to Houston Texans")

            nico.updated_at = datetime.now()
            updated_count += 1

        db.session.commit()
        print(f"\n✓ Updated {updated_count} players with enhanced data")

def update_player_from_data(player, data):
    """Update player record from ESPN data"""
    updated = False

    if not player.position and data.get('position'):
        player.position = data['position']
        updated = True
        print(f"  ✓ Updated position: {data['position']}")

    if not player.current_team and data.get('current_team'):
        player.current_team = data['current_team']
        updated = True
        print(f"  ✓ Updated team: {data['current_team']}")

    if not player.team_abbreviation and data.get('team_abbreviation'):
        player.team_abbreviation = data['team_abbreviation']
        updated = True
        print(f"  ✓ Updated team abbr: {data['team_abbreviation']}")

    if not player.jersey_number and data.get('jersey_number') and str(data['jersey_number']).isdigit():
        player.jersey_number = int(data['jersey_number'])
        updated = True
        print(f"  ✓ Updated jersey: {data['jersey_number']}")

    if updated:
        player.updated_at = datetime.now()

    return updated

if __name__ == '__main__':
    update_missing_player_data()