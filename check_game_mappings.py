#!/usr/bin/env python3
"""
Check for bet legs with game dates that are more than 3 days away from bet date.
This helps identify incorrectly mapped ESPN games.
"""

import os
import sys
from datetime import datetime, timedelta

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Bet, BetLeg

def check_incorrect_game_mappings():
    """Find bet legs where game_date is > 3 days from bet_date"""

    with app.app_context():
        print("=" * 80)
        print("CHECKING FOR INCORRECTLY MAPPED ESPN GAMES")
        print("=" * 80)
        print("Finding bet legs where game_date is more than 3 days from bet_date")
        print()

        # Query to join bets and bet_legs, calculate date difference
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

        print(f"Found {len(results)} total bet legs with game dates")

        problematic_legs = []

        for leg, bet_date_str, bet_type, betting_site, bet_id in results:
            try:
                # Parse bet_date string to datetime
                bet_date = datetime.strptime(bet_date_str, '%Y-%m-%d').date()

                # Calculate date difference
                if leg.game_date and bet_date:
                    days_diff = abs((leg.game_date - bet_date).days)

                    if days_diff > 3:
                        problematic_legs.append({
                            'bet_id': bet_id,
                            'bet_date': bet_date,
                            'game_date': leg.game_date,
                            'days_diff': days_diff,
                            'player': leg.player_name,
                            'team': leg.player_team,
                            'bet_type': bet_type,
                            'betting_site': betting_site,
                            'leg_bet_type': leg.bet_type,
                            'home_team': leg.home_team,
                            'away_team': leg.away_team,
                            'game_id': leg.game_id,
                            'sport': leg.sport
                        })

            except (ValueError, AttributeError) as e:
                print(f"Error parsing dates for bet {bet_id}, leg {leg.id}: {e}")
                continue

        print(f"\nFound {len(problematic_legs)} legs with game dates > 3 days from bet date")
        print()

        if problematic_legs:
            print("PROBLEMATIC LEGS:")
            print("-" * 80)

            # Sort by days difference (most problematic first)
            problematic_legs.sort(key=lambda x: x['days_diff'], reverse=True)

            for leg in problematic_legs:
                print(f"Bet ID: {leg['bet_id']}")
                print(f"  Bet Date: {leg['bet_date']} | Game Date: {leg['game_date']} | Days Diff: {leg['days_diff']}")
                print(f"  Player: {leg['player']} ({leg['team']})")
                print(f"  Bet Type: {leg['bet_type']} | Leg Type: {leg['leg_bet_type']}")
                print(f"  Game: {leg['away_team']} @ {leg['home_team']}")
                print(f"  Site: {leg['betting_site']} | Sport: {leg['sport']} | Game ID: {leg['game_id']}")
                print("-" * 40)

            # Summary by days difference
            print("\nSUMMARY BY DAYS DIFFERENCE:")
            diff_ranges = [(3, 7), (8, 14), (15, 30), (31, 365)]
            for min_days, max_days in diff_ranges:
                count = len([l for l in problematic_legs if min_days <= l['days_diff'] <= max_days])
                if count > 0:
                    print(f"  {min_days}-{max_days} days: {count} legs")

            very_old = len([l for l in problematic_legs if l['days_diff'] > 365])
            if very_old > 0:
                print(f"  > 1 year: {very_old} legs")

        else:
            print("✅ No problematic game date mappings found!")

        print("\n" + "=" * 80)

        return problematic_legs

if __name__ == "__main__":
    check_incorrect_game_mappings()