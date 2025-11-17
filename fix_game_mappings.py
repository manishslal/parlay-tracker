#!/usr/bin/env python3
"""
Fix incorrectly mapped ESPN games for bet legs.
This script finds bet legs with game dates > 3 days from bet date
and attempts to find the correct historical game that was actually played.
"""

import os
import sys
from datetime import datetime, timedelta

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Bet, BetLeg
from helpers.espn_api import get_espn_games_for_date, find_game_for_team

def fix_incorrect_game_mappings():
    """Fix bet legs with incorrect game date mappings"""

    with app.app_context():
        print("=" * 80)
        print("FIXING INCORRECTLY MAPPED ESPN GAMES")
        print("=" * 80)

        # Query to find problematic legs
        results = db.session.query(
            BetLeg,
            Bet.bet_date,
            Bet.bet_type,
            Bet.betting_site,
            Bet.id.label('bet_id')
        ).join(
            Bet, BetLeg.bet_id == Bet.id
        ).filter(
            BetLeg.game_date.isnot(None),
            Bet.bet_date.isnot(None),
            Bet.bet_date != ''
        ).all()

        print(f"Checking {len(results)} total bet legs...")

        fixed_count = 0
        error_count = 0

        for leg, bet_date_str, bet_type, betting_site, bet_id in results:
            try:
                # Parse bet_date
                bet_date = datetime.strptime(bet_date_str, '%Y-%m-%d').date()

                # Check if game_date is > 3 days from bet_date
                if leg.game_date and abs((leg.game_date - bet_date).days) > 3:
                    print(f"\n🔍 Fixing Bet {bet_id} Leg {leg.id}:")
                    print(f"   Bet Date: {bet_date} | Current Game Date: {leg.game_date}")
                    print(f"   Player: {leg.player_name} ({leg.player_team})")
                    print(f"   Game: {leg.away_team} @ {leg.home_team}")

                    # Try to find the correct game around the bet date
                    correct_game = None
                    search_dates = []

                    # Search within ±7 days of bet date
                    for days_offset in range(-7, 8):
                        search_date = bet_date + timedelta(days=days_offset)
                        search_dates.append(search_date)

                        try:
                            games = get_espn_games_for_date(search_date)
                            if games:
                                # Look for a game matching the teams
                                for game in games:
                                    away_team, home_team = game  # Unpack tuple
                                    game_id = ""  # No game ID in current API
                                    
                                    leg_away = (leg.away_team or '').upper()
                                    leg_home = (leg.home_team or '').upper()
                                    game_away = away_team.upper()
                                    game_home = home_team.upper()

                                    # Check if teams match (allowing for abbreviations)
                                    if ((game_away in leg_away or leg_away in game_away) and
                                        (game_home in leg_home or leg_home in game_home)) or \
                                       ((game_away in leg_home or leg_home in game_away) and
                                        (game_home in leg_away or leg_away in game_away)):
                                        correct_game = {
                                            'date': search_date,
                                            'game_id': game_id,
                                            'away_team': away_team,
                                            'home_team': home_team
                                        }
                                        break

                            if correct_game:
                                break

                        except Exception as e:
                            continue

                    if correct_game:
                        print(f"   ✅ Found correct game: {correct_game['away_team']} @ {correct_game['home_team']} on {correct_game['date']}")

                        # Update the leg with correct game info
                        leg.game_date = correct_game['date']
                        if correct_game['game_id']:
                            leg.game_id = str(correct_game['game_id'])

                        # Update team names if they differ
                        if correct_game['away_team'] and correct_game['away_team'] != leg.away_team:
                            leg.away_team = correct_game['away_team']
                        if correct_game['home_team'] and correct_game['home_team'] != leg.home_team:
                            leg.home_team = correct_game['home_team']

                        fixed_count += 1
                        print(f"   ✅ Updated leg with correct game date")

                    else:
                        print(f"   ❌ Could not find correct game within ±7 days of bet date")
                        error_count += 1

            except Exception as e:
                print(f"   ❌ Error processing leg {leg.id}: {e}")
                error_count += 1
                continue

        # Commit all changes
        try:
            db.session.commit()
            print(f"\n✅ Successfully fixed {fixed_count} bet legs")
            if error_count > 0:
                print(f"⚠️  Could not fix {error_count} bet legs")
        except Exception as e:
            print(f"❌ Error committing changes: {e}")
            db.session.rollback()

        print("\n" + "=" * 80)

        return fixed_count, error_count

if __name__ == "__main__":
    fix_incorrect_game_mappings()