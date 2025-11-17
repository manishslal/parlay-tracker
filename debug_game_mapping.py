#!/usr/bin/env python3
"""
Debug script to test finding correct games for one specific problematic bet leg.
This will help us understand why the bulk fix isn't working.
"""

import os
import sys
from datetime import datetime, timedelta

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Bet, BetLeg
from helpers.espn_api import get_espn_games_for_date, find_game_for_team

def debug_single_bet_leg(bet_id=51, leg_id=None):
    """Debug finding correct game for one specific bet leg"""

    with app.app_context():
        print("=" * 80)
        print("DEBUGGING SINGLE BET LEG GAME MAPPING")
        print("=" * 80)

        # Find the specific bet leg (using the first problematic one from our earlier results)
        if leg_id:
            leg = BetLeg.query.filter(BetLeg.id == leg_id).first()
        else:
            # Find first leg from bet 51
            bet = Bet.query.get(bet_id)
            if bet:
                legs = bet.bet_legs_rel
                leg = legs[0] if legs else None
            else:
                leg = None

        if not leg:
            print(f"❌ Could not find bet leg (bet_id={bet_id}, leg_id={leg_id})")
            return

        bet = Bet.query.get(leg.bet_id)
        bet_date = datetime.strptime(bet.bet_date, '%Y-%m-%d').date()

        print(f"🔍 Testing Bet {bet.id} Leg {leg.id}:")
        print(f"   Bet Date: {bet_date}")
        print(f"   Current Game Date: {leg.game_date}")
        print(f"   Days Difference: {abs((leg.game_date - bet_date).days) if leg.game_date else 'N/A'}")
        print(f"   Player: {leg.player_name} ({leg.player_team})")
        print(f"   Stored Teams: {leg.away_team} @ {leg.home_team}")
        print(f"   Game ID: {leg.game_id}")
        print()

        # Test different date ranges
        print("🧪 TESTING DIFFERENT SEARCH PARAMETERS:")
        print()

        test_ranges = [
            (-3, 3),    # ±3 days (very narrow)
            (-7, 7),    # ±7 days (current)
            (-14, 14),  # ±14 days (wider)
            (-30, 30),  # ±30 days (very wide)
        ]

        for min_days, max_days in test_ranges:
            print(f"📅 Testing range: {min_days} to {max_days} days from bet date")
            found_games = []

            for days_offset in range(min_days, max_days + 1):
                search_date = bet_date + timedelta(days=days_offset)

                try:
                    games = get_espn_games_for_date(search_date)
                    if games:
                        print(f"   Date {search_date}: Found {len(games)} games")
                        for game in games[:3]:  # Show first 3 games
                            away_team, home_team = game  # Unpack tuple
                            game_id = ""  # No game ID in current API

                            # Test team matching
                            leg_away = (leg.away_team or '').upper()
                            leg_home = (leg.home_team or '').upper()
                            game_away = away_team.upper()
                            game_home = home_team.upper()

                            # Check various matching criteria
                            matches = []

                            # Exact match
                            if game_away == leg_away and game_home == leg_home:
                                matches.append("EXACT")
                            elif game_away == leg_home and game_home == leg_away:  # Reversed
                                matches.append("REVERSED")

                            # Substring match
                            if (game_away in leg_away or leg_away in game_away) and \
                               (game_home in leg_home or leg_home in game_home):
                                matches.append("SUBSTRING")

                            if matches:
                                found_games.append({
                                    'date': search_date,
                                    'away_team': away_team,
                                    'home_team': home_team,
                                    'game_id': game_id,
                                    'matches': matches
                                })
                                print(f"     🎯 MATCH {matches}: {away_team} @ {home_team} (ID: {game_id})")

                    else:
                        print(f"   Date {search_date}: No games found")

                except Exception as e:
                    print(f"   Date {search_date}: Error - {e}")

            print(f"   → Found {len(found_games)} potential matches in this range")
            print()

        # Test the current stored game ID
        if leg.game_id:
            print(f"🔍 TESTING CURRENT GAME ID: {leg.game_id}")
            # We could add logic here to fetch game details by ID
            print("   (Would need to implement game lookup by ID)")
        print()

        print("💡 RECOMMENDATIONS:")
        print("   1. If no games found: ESPN may not have historical data for these dates")
        print("   2. If games found but no matches: Team name normalization needed")
        print("   3. If matches found: Current search logic may be too restrictive")
        print("   4. Consider manual mapping for very old bets")

        print("\n" + "=" * 80)

if __name__ == "__main__":
    # Test with the first problematic bet from our earlier results
    debug_single_bet_leg(bet_id=51)