#!/usr/bin/env python3
"""
Comprehensive fix for incorrectly mapped ESPN games.
This version uses multiple strategies to find correct games.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, List

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Bet, BetLeg
from helpers.espn_api import get_espn_games_for_date, get_espn_games_with_ids_for_date

# Team name normalization mapping
TEAM_NAME_MAPPING = {
    # Full names to abbreviations
    'Arizona Cardinals': 'ARI',
    'Atlanta Falcons': 'ATL',
    'Baltimore Ravens': 'BAL',
    'Buffalo Bills': 'BUF',
    'Carolina Panthers': 'CAR',
    'Chicago Bears': 'CHI',
    'Cincinnati Bengals': 'CIN',
    'Cleveland Browns': 'CLE',
    'Dallas Cowboys': 'DAL',
    'Denver Broncos': 'DEN',
    'Detroit Lions': 'DET',
    'Green Bay Packers': 'GB',
    'Houston Texans': 'HOU',
    'Indianapolis Colts': 'IND',
    'Jacksonville Jaguars': 'JAX',
    'Kansas City Chiefs': 'KC',
    'Las Vegas Raiders': 'LV',
    'Los Angeles Chargers': 'LAC',
    'Los Angeles Rams': 'LAR',
    'Miami Dolphins': 'MIA',
    'Minnesota Vikings': 'MIN',
    'New England Patriots': 'NE',
    'New Orleans Saints': 'NO',
    'New York Giants': 'NYG',
    'New York Jets': 'NYJ',
    'Philadelphia Eagles': 'PHI',
    'Pittsburgh Steelers': 'PIT',
    'San Francisco 49ers': 'SF',
    'Seattle Seahawks': 'SEA',
    'Tampa Bay Buccaneers': 'TB',
    'Tennessee Titans': 'TEN',
    'Washington Commanders': 'WSH',

    # Abbreviations to full names
    'ARI': 'Arizona Cardinals',
    'ATL': 'Atlanta Falcons',
    'BAL': 'Baltimore Ravens',
    'BUF': 'Buffalo Bills',
    'CAR': 'Carolina Panthers',
    'CHI': 'Chicago Bears',
    'CIN': 'Cincinnati Bengals',
    'CLE': 'Cleveland Browns',
    'DAL': 'Dallas Cowboys',
    'DEN': 'Denver Broncos',
    'DET': 'Detroit Lions',
    'GB': 'Green Bay Packers',
    'HOU': 'Houston Texans',
    'IND': 'Indianapolis Colts',
    'JAX': 'Jacksonville Jaguars',
    'KC': 'Kansas City Chiefs',
    'LV': 'Las Vegas Raiders',
    'LAC': 'Los Angeles Chargers',
    'LAR': 'Los Angeles Rams',
    'MIA': 'Miami Dolphins',
    'MIN': 'Minnesota Vikings',
    'NE': 'New England Patriots',
    'NO': 'New Orleans Saints',
    'NYG': 'New York Giants',
    'NYJ': 'New York Jets',
    'PHI': 'Philadelphia Eagles',
    'PIT': 'Pittsburgh Steelers',
    'SF': 'San Francisco 49ers',
    'SEA': 'Seattle Seahawks',
    'TB': 'Tampa Bay Buccaneers',
    'TEN': 'Tennessee Titans',
    'WSH': 'Washington Commanders',

    # Alternative names
    'Washington Football Team': 'Washington Commanders',
    'Washington Redskins': 'Washington Commanders',
    'Oakland Raiders': 'Las Vegas Raiders',
    'San Diego Chargers': 'Los Angeles Chargers',
    'St. Louis Rams': 'Los Angeles Rams',
    'Cleveland Browns': 'Cleveland Browns',
    'Canton Bulldogs': 'Cleveland Browns',  # Historical
}

def normalize_team_name(team_name: str) -> str:
    """Normalize team name to canonical form."""
    if not team_name:
        return ""

    # Clean the name
    name = team_name.strip().upper()

    # Check direct mapping
    if name in TEAM_NAME_MAPPING:
        return TEAM_NAME_MAPPING[name]

    # Check if it's already a canonical name
    for canonical, abbrev in TEAM_NAME_MAPPING.items():
        if name == canonical.upper() or name == abbrev:
            return canonical

    # Try partial matches
    for canonical in TEAM_NAME_MAPPING.keys():
        if len(canonical) > 3:  # Skip abbreviations
            if canonical.upper() in name or name in canonical.upper():
                return canonical

    return team_name  # Return original if no match

def find_game_for_player_team(player_team: str, bet_date: datetime, max_search_days: int = 30) -> Optional[Dict]:
    """
    Find a game for a player's team around the bet date.
    Prioritizes games within 5 days, then expands search if needed.
    Returns game info if found, None otherwise.
    """
    normalized_team = normalize_team_name(player_team)
    if not normalized_team:
        return None

    # Phase 1: Search within 5 days (user's requirement)
    print(f"   🔍 Phase 1: Searching within 5 days of bet date...")
    for days_offset in range(-5, 6):  # -5 to +5 days
        check_date = bet_date + timedelta(days=days_offset)

        try:
            games = get_espn_games_with_ids_for_date(check_date)
            if games:
                for game_id, away_team, home_team in games:
                    # Check if player's team is playing
                    if (normalize_team_name(away_team) == normalized_team or
                        normalize_team_name(home_team) == normalized_team):
                        return {
                            'game_id': game_id,
                            'date': check_date,
                            'away_team': away_team,
                            'home_team': home_team,
                            'player_team': normalized_team,
                            'days_from_bet': abs(days_offset),
                            'is_home': normalize_team_name(home_team) == normalized_team
                        }
        except Exception as e:
            continue

    print(f"   ⚠️ No games found within 5 days, expanding search...")

    # Phase 2: Search within wider window (up to max_search_days)
    for days_offset in range(-max_search_days, max_search_days + 1):
        if abs(days_offset) <= 5:  # Skip days we already checked
            continue

        check_date = bet_date + timedelta(days=days_offset)

        try:
            games = get_espn_games_with_ids_for_date(check_date)
            if games:
                for game_id, away_team, home_team in games:
                    # Check if player's team is playing
                    if (normalize_team_name(away_team) == normalized_team or
                        normalize_team_name(home_team) == normalized_team):
                        return {
                            'game_id': game_id,
                            'date': check_date,
                            'away_team': away_team,
                            'home_team': home_team,
                            'player_team': normalized_team,
                            'days_from_bet': abs(days_offset),
                            'is_home': normalize_team_name(home_team) == normalized_team
                        }
        except Exception as e:
            continue

    return None

def find_game_by_stored_teams(away_team: str, home_team: str, bet_date: datetime, search_window_days: int = 14) -> Optional[Dict]:
    """
    Find a game by matching stored away/home teams.
    """
    if not away_team or not home_team:
        return None

    normalized_away = normalize_team_name(away_team)
    normalized_home = normalize_team_name(home_team)

    # Search within window of bet date
    for days_offset in range(-search_window_days, search_window_days + 1):
        check_date = bet_date + timedelta(days=days_offset)

        try:
            games = get_espn_games_with_ids_for_date(check_date)
            if games:
                for game_id, game_away, game_home in games:
                    # Check for exact match (allowing for team name variations)
                    game_away_norm = normalize_team_name(game_away)
                    game_home_norm = normalize_team_name(game_home)

                    if ((game_away_norm == normalized_away and game_home_norm == normalized_home) or
                        (game_away_norm == normalized_home and game_home_norm == normalized_away)):
                        return {
                            'game_id': game_id,
                            'date': check_date,
                            'away_team': game_away,
                            'home_team': game_home,
                            'stored_away': away_team,
                            'stored_home': home_team
                        }
        except Exception as e:
            continue

    return None

def comprehensive_fix_game_mapping():
    """Fix game mappings using multiple strategies."""

    with app.app_context():
        print("=" * 100)
        print("COMPREHENSIVE GAME MAPPING FIX")
        print("=" * 100)

        # Get all bet legs with game dates
        results = db.session.query(
            BetLeg,
            Bet.bet_date,
            Bet.id.label('bet_id')
        ).join(
            Bet, BetLeg.bet_id == Bet.id
        ).filter(
            BetLeg.game_date.isnot(None),
            Bet.bet_date.isnot(None),
            Bet.bet_date != ''
        ).all()

        print(f"Found {len(results)} total bet legs with game dates")

        problematic_legs = []
        for leg, bet_date_str, bet_id in results:
            try:
                bet_date = datetime.strptime(bet_date_str, '%Y-%m-%d').date()
                if leg.game_date and abs((leg.game_date - bet_date).days) > 3:
                    problematic_legs.append((leg, bet_date, bet_id))
            except (ValueError, AttributeError):
                continue

        print(f"Found {len(problematic_legs)} legs with game dates > 3 days from bet date")
        print()

        fixed_count = 0
        error_count = 0
        strategy_counts = {'player_team': 0, 'stored_teams': 0, 'not_found': 0}

        for leg, bet_date, bet_id in problematic_legs:
            print(f"\n🔍 Fixing Bet {bet_id} Leg {leg.id}:")
            print(f"   Bet Date: {bet_date} | Current Game Date: {leg.game_date} ({abs((leg.game_date - bet_date).days)} days)")
            print(f"   Player: {leg.player_name} ({leg.player_team})")
            print(f"   Stored teams: {leg.away_team} @ {leg.home_team}")

            correct_game = None
            strategy_used = None

            # Strategy 1: Use player's team to find game
            if leg.player_team:
                print(f"   📊 Strategy 1: Searching by player team '{leg.player_team}'...")
                correct_game = find_game_for_player_team(leg.player_team, bet_date)
                if correct_game:
                    strategy_used = 'player_team'
                    print(f"   ✅ Found game: {correct_game['away_team']} @ {correct_game['home_team']} on {correct_game['date']}")

            # Strategy 2: Use stored team information (if Strategy 1 failed)
            if not correct_game and leg.away_team and leg.home_team:
                print(f"   📊 Strategy 2: Searching by stored teams '{leg.away_team} @ {leg.home_team}'...")
                correct_game = find_game_by_stored_teams(leg.away_team, leg.home_team, bet_date)
                if correct_game:
                    strategy_used = 'stored_teams'
                    print(f"   ✅ Found game: {correct_game['away_team']} @ {correct_game['home_team']} on {correct_game['date']}")

            # Update the database if we found a correct game
            if correct_game:
                try:
                    leg.game_date = correct_game['date']
                    leg.away_team = correct_game['away_team']
                    leg.home_team = correct_game['home_team']
                    leg.game_id = correct_game['game_id']  # Set the correct ESPN game ID

                    db.session.commit()
                    fixed_count += 1
                    strategy_counts[strategy_used] += 1
                    print(f"   ✅ Updated leg with correct game date and ESPN game ID using {strategy_used} strategy")
                except Exception as e:
                    db.session.rollback()
                    error_count += 1
                    print(f"   ❌ Error updating database: {e}")
            else:
                strategy_counts['not_found'] += 1
                print(f"   ❌ No correct game found for this leg")

        # Commit all changes
        try:
            db.session.commit()
            print(f"\n✅ Successfully fixed {fixed_count} bet legs")
            print("Strategy breakdown:")
            for strategy, count in strategy_counts.items():
                print(f"   {strategy}: {count} legs")
            if error_count > 0:
                print(f"⚠️  Could not fix {error_count} bet legs")
        except Exception as e:
            print(f"❌ Error committing changes: {e}")
            db.session.rollback()

        print("\n" + "=" * 100)

        return fixed_count, error_count, strategy_counts

if __name__ == "__main__":
    comprehensive_fix_game_mapping()