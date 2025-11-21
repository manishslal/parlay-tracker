#!/usr/bin/env python3
"""
Manual fix script for OCR-uploaded SGP bet
Run this on Render to connect the bet to ESPN API for live data
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Bet, BetLeg
from helpers.espn_api import get_espn_games_with_ids_for_date
from services import populate_player_data_for_bet
from datetime import datetime

def find_recent_ocr_bet():
    """Find the most recent OCR-uploaded bet (likely the SGP bet)"""
    with app.app_context():
        # Look for recent bets that haven't been processed by API yet
        recent_bets = Bet.query.filter(
            Bet.api_fetched == 'No',
            Bet.created_at >= datetime.now().replace(hour=0, minute=0, second=0)  # Today
        ).order_by(Bet.created_at.desc()).all()

        print(f"Found {len(recent_bets)} recent unprocessed bets:")

        for bet in recent_bets:
            print(f"\nBet ID: {bet.id}")
            print(f"  Created: {bet.created_at}")
            print(f"  Type: {bet.bet_type}")
            print(f"  Legs: {len(bet.bet_legs_rel) if bet.bet_legs_rel else 0}")

            if bet.bet_legs_rel:
                has_moneyline = any(leg.stat_type == 'moneyline' for leg in bet.bet_legs_rel)
                has_player_prop = any(leg.stat_type not in ['moneyline', 'spread', 'total_points'] for leg in bet.bet_legs_rel)

                if has_moneyline and has_player_prop:
                    print("  ✅ This looks like the SGP bet (moneyline + player prop)")
                    return bet
                elif len(bet.bet_legs_rel) > 1:
                    print("  ⚠️  Multiple legs - could be the SGP bet")
                    return bet

        print("\n❌ No obvious SGP bet found")
        return None

def fix_bet_game_ids(bet):
    """Manually populate game IDs for the bet"""
    print(f"\n🔧 Fixing game IDs for bet {bet.id}")

    # Get all legs for this bet
    bet_legs = BetLeg.query.filter(BetLeg.bet_id == bet.id).order_by(BetLeg.leg_order).all()

    if not bet_legs:
        print("❌ No legs found for this bet")
        return False

    print(f"Found {len(bet_legs)} legs to process")

    # Group legs by game date
    legs_by_date = {}
    for leg in bet_legs:
        if leg.game_date:
            date_key = leg.game_date
            if date_key not in legs_by_date:
                legs_by_date[date_key] = []
            legs_by_date[date_key].append(leg)

    print(f"Processing {len(legs_by_date)} different game dates")

    # Process each date
    total_fixed = 0
    for game_date, legs in legs_by_date.items():
        print(f"\n📅 Processing date: {game_date}")

        try:
            # Get games with IDs for this date
            games = get_espn_games_with_ids_for_date(game_date)
            if not games:
                print(f"❌ No games found for date {game_date}")
                continue

            print(f"Found {len(games)} games for {game_date}")

            # Try to match each leg to a game
            for leg in legs:
                print(f"  🎯 Processing leg {leg.id}: {leg.player_name} ({leg.player_team}) vs {leg.away_team}")

                # For SGP bets, all legs should be for the same game
                # Try to find the game by matching teams
                matched_game = None

                for game in games:
                    game_teams = game.get('teams', {})
                    home_team = game_teams.get('home', '').lower()
                    away_team = game_teams.get('away', '').lower()

                    # Check if this leg's teams match the game
                    leg_home = (leg.home_team or '').lower()
                    leg_away = (leg.away_team or '').lower()
                    leg_player_team = (leg.player_team or '').lower()

                    # For moneyline: player_team should be the bet team
                    # For player props: player_team should be the player's team
                    if leg.stat_type == 'moneyline':
                        # Moneyline bet on a team
                        if (leg_player_team in home_team or home_team in leg_player_team) and leg_away == 'tbd':
                            # This is likely the game - update the away team
                            matched_game = game
                            leg.away_team = game_teams.get('away', '')
                            print(f"    ✅ Matched moneyline: {leg.player_team} vs {leg.away_team}")
                            break
                        elif (leg_player_team in away_team or away_team in leg_player_team) and leg_away == 'tbd':
                            matched_game = game
                            leg.away_team = game_teams.get('home', '')
                            print(f"    ✅ Matched moneyline: {leg.player_team} vs {leg.away_team}")
                            break
                    else:
                        # Player prop - check if player_team matches either home or away
                        if leg_player_team and (leg_player_team in home_team or home_team in leg_player_team):
                            matched_game = game
                            # Update teams to match the game
                            leg.home_team = game_teams.get('home', '')
                            leg.away_team = game_teams.get('away', '')
                            print(f"    ✅ Matched player prop: {leg.player_team} in game {home_team} vs {away_team}")
                            break
                        elif leg_player_team and (leg_player_team in away_team or away_team in leg_player_team):
                            matched_game = game
                            leg.home_team = game_teams.get('away', '')  # Swap if player is on away team
                            leg.away_team = game_teams.get('home', '')
                            print(f"    ✅ Matched player prop: {leg.player_team} in game {away_team} vs {home_team}")
                            break

                if matched_game:
                    # Update the leg with game info
                    leg.game_id = str(matched_game.get('espn_game_id', ''))
                    leg.game_status = matched_game.get('statusTypeName', 'STATUS_SCHEDULED')
                    total_fixed += 1
                    print(f"    📊 Updated leg with game ID: {leg.game_id}")
                else:
                    print(f"    ❌ Could not match leg to any game")

        except Exception as e:
            print(f"❌ Error processing date {game_date}: {e}")
            continue

    # Commit changes
    if total_fixed > 0:
        db.session.commit()
        print(f"\n✅ Successfully updated {total_fixed} legs with game IDs")
        return True
    else:
        print("\n❌ No legs were updated")
        return False

def populate_bet_data(bet):
    """Populate player data and update the bet"""
    print(f"\n🎯 Populating player data for bet {bet.id}")

    try:
        # Populate player data
        populate_player_data_for_bet(bet)
        print("✅ Player data populated")

        # Mark bet as processed
        bet.api_fetched = 'Yes'
        db.session.commit()
        print("✅ Bet marked as API fetched")

        return True
    except Exception as e:
        print(f"❌ Error populating bet data: {e}")
        db.session.rollback()
        return False

def main():
    print("🔧 Manual SGP Bet Fix Script")
    print("=" * 40)

    # Find the bet
    bet = find_recent_ocr_bet()
    if not bet:
        print("❌ Could not find the SGP bet to fix")
        return

    # Fix game IDs
    if fix_bet_game_ids(bet):
        # Populate player data
        if populate_bet_data(bet):
            print("\n🎉 SUCCESS: Bet has been connected to ESPN API!")
            print("   The bet should now show live data on the frontend.")
            print("   Check the app to see updated scores and status.")
        else:
            print("\n⚠️  Game IDs were fixed but player data population failed")
    else:
        print("\n❌ Failed to fix game IDs for the bet")

if __name__ == "__main__":
    main()