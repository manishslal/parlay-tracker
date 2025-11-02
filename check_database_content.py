#!/usr/bin/env python3
"""
Check what's actually in the PostgreSQL bet_data column
"""
import json
from app import app, db
from models import Bet

def check_database_content():
    """Check actual database content"""
    
    with app.app_context():
        # Get first 5 historical bets
        bets = Bet.query.filter_by(status='completed').limit(5).all()
        
        print(f"📊 Checking {len(bets)} historical bets in PostgreSQL\n")
        
        for bet in bets:
            print(f"\n{'='*70}")
            print(f"Bet ID: {bet.id}")
            print(f"Bet Name: {bet.get_bet_data().get('name')}")
            print(f"API Fetched: {bet.api_fetched}")
            print('='*70)
            
            bet_data = bet.get_bet_data()
            
            print(f"\nTotal legs: {len(bet_data.get('legs', []))}")
            
            if bet_data.get('legs'):
                first_leg = bet_data['legs'][0]
                print(f"\nFirst leg structure:")
                print(f"  Keys present: {list(first_leg.keys())}")
                print(f"  Player: {first_leg.get('player', 'N/A')}")
                print(f"  Line/Target: {first_leg.get('line') or first_leg.get('target', 'N/A')}")
                
                # Check for ESPN data fields
                espn_fields = ['current', 'status', 'result', 'final_value', 'score']
                print(f"\n  ESPN data fields:")
                for field in espn_fields:
                    if field in first_leg:
                        print(f"    ✅ {field}: {first_leg[field]}")
                    else:
                        print(f"    ❌ {field}: MISSING")
            
            # Check if bet_data JSON string contains 'current'
            bet_data_str = bet.bet_data
            has_current_in_json = 'current' in bet_data_str.lower()
            print(f"\n  'current' in bet_data JSON: {'✅ YES' if has_current_in_json else '❌ NO'}")

if __name__ == '__main__':
    check_database_content()
