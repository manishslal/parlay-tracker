#!/usr/bin/env python3
"""
Test script to directly test the bet slip database save functionality.
This bypasses the web API and tests the core save_bet_to_db function.
"""

import sys
import os
sys.path.append('/Users/manishslal/Desktop/Scrapper')

from dotenv import load_dotenv
load_dotenv()

from app import app, db, save_bet_to_db

def test_simple_bet_leg_creation():
    """Test creating a single BetLeg to isolate the issue."""
    from models import BetLeg

    with app.app_context():
        try:
            print('🧪 Testing simple BetLeg creation...')

            # Create a minimal BetLeg
            bet_leg = BetLeg(
                bet_id=1,  # Assume bet_id 1 exists
                player_name='Test Player',
                home_team='Test Home',
                away_team='Test Away',
                bet_type='spread',
                target_value=5.0,
                status='pending'
            )

            db.session.add(bet_leg)
            db.session.commit()

            print('✅ BetLeg created successfully!')
            print(f'   - ID: {bet_leg.id}')
            return True

        except Exception as e:
            print(f'❌ BetLeg creation failed: {e}')
            db.session.rollback()
            return False

def test_database_save():
    """Test saving bet data directly to the database."""

    # Use the transformed data that our function produces
    bet_data = {
        'wager': 10.0,
        'potential_winnings': 35.0,
        'final_odds': '+250',
        'bet_date': None,
        'betting_site_id': 'DraftKings',
        'bet_type': 'parlay',
        'legs': [
            {
                'player_name': None,
                'team_name': 'Los Angeles Lakers',
                'stat_type': 'spread',
                'bet_type': 'spread',
                'target_value': -4.5,
                'bet_line_type': None,
                'odds': None,
                'home_team': 'Los Angeles Lakers',
                'away_team': 'TBD',
                'sport': 'NBA'
            },
            {
                'player_name': None,
                'team_name': 'Boston Celtics',
                'stat_type': 'moneyline',
                'bet_type': 'moneyline',
                'target_value': 0,
                'bet_line_type': None,
                'odds': None,
                'home_team': 'Boston Celtics',
                'away_team': 'TBD',
                'sport': 'NBA'
            },
            {
                'player_name': None,
                'team_name': 'Game Total',
                'stat_type': 'total_points',
                'bet_type': 'total',
                'target_value': 220.5,
                'bet_line_type': 'over',
                'odds': None,
                'home_team': 'Game Total',
                'away_team': 'Game Total',
                'sport': 'NFL'
            }
        ]
    }

    with app.app_context():
        try:
            print('🧪 Testing direct database save...')
            print('📊 Bet data to save:')
            print(f'   - Wager: {bet_data["wager"]}')
            print(f'   - Odds: {bet_data["final_odds"]}')
            print(f'   - Legs: {len(bet_data["legs"])}')

            # Test user ID - adjust this to a valid user in your database
            test_user_id = 1

            result = save_bet_to_db(test_user_id, bet_data, skip_duplicate_check=True)

            print('✅ Save successful!')
            print('📋 Saved bet info:')
            print(f'   - Bet ID: {result.get("id")}')
            print(f'   - Status: {result.get("status")}')
            print(f'   - Legs: {len(result.get("legs", []))}')

            # Verify the bet was actually saved
            from models import Bet
            saved_bet = Bet.query.get(result.get('id'))
            if saved_bet:
                print('✅ Bet verified in database!')
                print(f'   - Database wager: {saved_bet.wager}')
                print(f'   - Database odds: {saved_bet.final_odds}')
                print(f'   - Database legs: {len(saved_bet.bet_legs_rel)}')
            else:
                print('❌ Bet not found in database after save!')

            return True

        except Exception as e:
            print(f'❌ Save failed: {e}')
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print('Testing simple BetLeg creation first...')
    simple_success = test_simple_bet_leg_creation()

    if simple_success:
        print('\nNow testing full bet save...')
        success = test_database_save()
    else:
        print('\nSkipping full bet save test due to BetLeg creation failure')
        success = False

    if success:
        print('\n🎉 All database tests PASSED!')
        print('✅ Bet slip OCR database integration is working!')
    else:
        print('\n❌ Database tests FAILED!')
        print('❌ There are still issues with the database save functionality')