#!/usr/bin/env python3
"""
Individual leg fix for incorrectly mapped ESPN games.
This version fixes each leg individually based on its specific player/team.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Bet, BetLeg
from helpers.espn_api import get_espn_games_for_date

# Team name normalization mapping (same as before)
TEAM_NAME_MAPPING = {
    'Arizona Cardinals': 'ARI', 'Atlanta Falcons': 'ATL', 'Baltimore Ravens': 'BAL',
    'Buffalo Bills': 'BUF', 'Carolina Panthers': 'CAR', 'Chicago Bears': 'CHI',
    'Cincinnati Bengals': 'CIN', 'Cleveland Browns': 'CLE', 'Dallas Cowboys': 'DAL',
    'Denver Broncos': 'DEN', 'Detroit Lions': 'DET', 'Green Bay Packers': 'GB',
    'Houston Texans': 'HOU', 'Indianapolis Colts': 'IND', 'Jacksonville Jaguars': 'JAX',
    'Kansas City Chiefs': 'KC', 'Las Vegas Raiders': 'LV', 'Los Angeles Chargers': 'LAC',
    'Los Angeles Rams': 'LAR', 'Miami Dolphins': 'MIA', 'Minnesota Vikings': 'MIN',
    'New England Patriots': 'NE', 'New Orleans Saints': 'NO', 'New York Giants': 'NYG',
    'New York Jets': 'NYJ', 'Philadelphia Eagles': 'PHI', 'Pittsburgh Steelers': 'PIT',
    'San Francisco 49ers': 'SF', 'Seattle Seahawks': 'SEA', 'Tampa Bay Buccaneers': 'TB',
    'Tennessee Titans': 'TEN', 'Washington Commanders': 'WSH',
    'ARI': 'Arizona Cardinals', 'ATL': 'Atlanta Falcons', 'BAL': 'Baltimore Ravens',
    'BUF': 'Buffalo Bills', 'CAR': 'Carolina Panthers', 'CHI': 'Chicago Bears',
    'CIN': 'Cincinnati Bengals', 'CLE': 'Cleveland Browns', 'DAL': 'Dallas Cowboys',
    'DEN': 'Denver Broncos', 'DET': 'Detroit Lions', 'GB': 'Green Bay Packers',
    'HOU': 'Houston Texans', 'IND': 'Indianapolis Colts', 'JAX': 'Jacksonville Jaguars',
    'KC': 'Kansas City Chiefs', 'LV': 'Las Vegas Raiders', 'LAC': 'Los Angeles Chargers',
    'LAR': 'Los Angeles Rams', 'MIA': 'Miami Dolphins', 'MIN': 'Minnesota Vikings',
    'NE': 'New England Patriots', 'NO': 'New Orleans Saints', 'NYG': 'New York Giants',
    'NYJ': 'New York Jets', 'PHI': 'Philadelphia Eagles', 'PIT': 'Pittsburgh Steelers',
    'SF': 'San Francisco 49ers', 'SEA': 'Seattle Seahawks', 'TB': 'Tampa Bay Buccaneers',
    'TEN': 'Tennessee Titans', 'WSH': 'Washington Commanders',
}

def normalize_team_name(team_name: str) -> str:
    """Normalize team name to canonical form."""
    if not team_name:
        return ""
    name = team_name.strip().upper()
    if name in TEAM_NAME_MAPPING:
        return TEAM_NAME_MAPPING[name]
    for canonical in TEAM_NAME_MAPPING.keys():
        if len(canonical) > 3:
            if canonical.upper() in name or name in canonical.upper():
                return canonical
    return team_name

def find_game_for_leg(leg: BetLeg, bet_date: datetime, search_window_days: int = 30) -> Optional[Dict]:
    """
    Find the correct game for an individual bet leg.
    Uses the leg's player_team to find the appropriate game.
    """
    if not leg.player_team:
        return None

    normalized_team = normalize_team_name(leg.player_team)

    # Search within window of bet date
    for days_offset in range(-search_window_days, search_window_days + 1):
        check_date = bet_date + timedelta(days=days_offset)

        try:
            games = get_espn_games_for_date(check_date)
            if games:
                for game in games:
                    away_team, home_team = game

                    # Check if the leg's player team is playing
                    if (normalize_team_name(away_team) == normalized_team or
                        normalize_team_name(home_team) == normalized_team):
                        return {
                            'date': check_date,
                            'away_team': away_team,
                            'home_team': home_team,
                            'player_team': normalized_team,
                            'is_home': normalize_team_name(home_team) == normalized_team
                        }
        except Exception as e:
            continue

    return None

def fix_individual_legs():
    """Fix each problematic leg individually."""

    with app.app_context():
        print("=" * 100)
        print("INDIVIDUAL LEG GAME MAPPING FIX")
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

        for leg, bet_date, bet_id in problematic_legs:
            print(f"\n🔍 Fixing Bet {bet_id} Leg {leg.id}:")
            print(f"   Bet Date: {bet_date} | Current Game Date: {leg.game_date} ({abs((leg.game_date - bet_date).days)} days)")
            print(f"   Player: {leg.player_name} ({leg.player_team})")

            # Find correct game for this specific leg
            correct_game = find_game_for_leg(leg, bet_date)

            if correct_game:
                try:
                    leg.game_date = correct_game['date']
                    leg.away_team = correct_game['away_team']
                    leg.home_team = correct_game['home_team']
                    leg.game_id = None  # Clear game ID

                    fixed_count += 1
                    print(f"   ✅ Updated leg: {correct_game['away_team']} @ {correct_game['home_team']} on {correct_game['date']}")

                except Exception as e:
                    print(f"   ❌ Error updating leg: {e}")
                    error_count += 1
            else:
                print(f"   ❌ Could not find correct game for {leg.player_team}")
                error_count += 1

        # Commit all changes
        try:
            db.session.commit()
            print(f"\n✅ Successfully fixed {fixed_count} bet legs")
            if error_count > 0:
                print(f"⚠️  Could not fix {error_count} bet legs")
        except Exception as e:
            print(f"❌ Error committing changes: {e}")
            db.session.rollback()

        print("\n" + "=" * 100)

        return fixed_count, error_count

if __name__ == "__main__":
    fix_individual_legs()