#!/usr/bin/env python3
"""
Enhanced player search with fallback strategies for ESPN API
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
from helpers.espn_api import search_espn_player, get_espn_player_details

def search_espn_by_last_name(last_name: str, sport: str = "football", league: str = "nfl") -> list:
    """
    Search ESPN by last name only to find potential matches
    """
    try:
        search_url = "https://site.api.espn.com/apis/search/v2"
        params = {
            "query": last_name,
            "limit": 15,  # Get more results for last name searches
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

def enhanced_player_search(player_name: str, sport: str = "football", league: str = "nfl") -> dict:
    """
    Enhanced player search with multiple fallback strategies

    Args:
        player_name: Name of the player to search for
        sport: Sport (default: "football")
        league: League (default: "nfl")

    Returns:
        Dictionary with player details or None if not found
    """
    print(f"Enhanced search for player: {player_name}")

    # Strategy 1: Full name search (original method)
    player_data = search_espn_player(player_name, sport=sport, league=league)
    if player_data and player_data.get('espn_player_id'):
        print(f"  ✓ Found by full name: {player_data['player_name']}")
        return player_data

    # Strategy 2: Last name search with first name initial matching
    name_parts = player_name.split()
    if len(name_parts) >= 2:
        last_name = name_parts[-1]
        first_initial = name_parts[0][0].upper()

        print(f"  Trying last name search: {last_name} with initial {first_initial}")

        # Search by last name
        last_name_results = search_espn_by_last_name(last_name, sport, league)

        # Filter by first name initial
        matching_candidates = []
        for candidate in last_name_results:
            candidate_name_parts = candidate['player_name'].split()
            if candidate_name_parts and candidate_name_parts[0][0].upper() == first_initial:
                matching_candidates.append(candidate)

        if matching_candidates:
            # Take the first match (most relevant)
            candidate = matching_candidates[0]
            print(f"  ✓ Found by last name + initial: {candidate['player_name']}")

            # Try to get detailed data for better accuracy
            if candidate.get('espn_player_id'):
                detailed_data = get_espn_player_details(candidate['espn_player_id'], sport, league)
                if detailed_data:
                    return detailed_data

            return candidate

    # Strategy 3: Try common name variations
    name_variations = generate_name_variations(player_name)
    for variation in name_variations:
        if variation != player_name:  # Don't repeat the original
            print(f"  Trying name variation: {variation}")
            variation_data = search_espn_player(variation, sport=sport, league=league)
            if variation_data and variation_data.get('espn_player_id'):
                print(f"  ✓ Found with variation: {variation_data['player_name']}")
                return variation_data

    # Strategy 4: Try partial name matches (first + last name parts)
    if len(name_parts) >= 2:
        # Try first name + last name without middle names
        simplified_name = f"{name_parts[0]} {name_parts[-1]}"
        if simplified_name != player_name:
            print(f"  Trying simplified name: {simplified_name}")
            simplified_data = search_espn_player(simplified_name, sport=sport, league=league)
            if simplified_data and simplified_data.get('espn_player_id'):
                print(f"  ✓ Found with simplified name: {simplified_data['player_name']}")
                return simplified_data

    print(f"  ✗ No matches found for {player_name}")
    return None

def search_espn_by_last_name(last_name: str, sport: str = "football", league: str = "nfl") -> list:
    """
    Search ESPN by last name only to find potential matches
    """
    try:
        search_url = "https://site.api.espn.com/apis/search/v2"
        params = {
            "query": last_name,
            "limit": 15,  # Get more results for last name searches
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

def generate_name_variations(player_name: str) -> list:
    """
    Generate common name variations to try
    """
    variations = []
    name_parts = player_name.split()

    if len(name_parts) >= 2:
        # Add Jr., Sr., III, etc. variations
        suffixes = ['Jr.', 'Sr.', 'III', 'II', 'IV']
        for suffix in suffixes:
            variations.append(f"{player_name} {suffix}")

        # Try without middle names/initials
        if len(name_parts) > 2:
            variations.append(f"{name_parts[0]} {name_parts[-1]}")

        # Try with different initials
        if len(name_parts[1]) == 1:  # Middle initial
            # Try without middle initial
            variations.append(f"{name_parts[0]} {name_parts[-1]}")

    return variations