#!/usr/bin/env python3
"""
Test Local Migration
Quick test to verify migration works on local PostgreSQL
"""

import os
import sys

# Set local database
os.environ['DATABASE_URL'] = 'postgresql://manishslal@localhost/parlays_local'

def test_migration():
    print("=" * 70)
    print("🧪 TESTING LOCAL MIGRATION")
    print("=" * 70)
    
    # Check database has data
    from app import app, db
    from models import User, Bet
    
    with app.app_context():
        user_count = User.query.count()
        bet_count = Bet.query.count()
        
        print(f"\n📊 Current database state:")
        print(f"   Users: {user_count}")
        print(f"   Bets: {bet_count}")
        
        if bet_count == 0:
            print("\n⚠️  No bets in database!")
            print("   Run import_production_data.py first to get test data")
            return
        
        # Show a sample bet
        sample_bet = Bet.query.first()
        print(f"\n📋 Sample bet data:")
        bet_data = sample_bet.get_bet_data()
        print(f"   Bet ID: {bet_data.get('bet_id', 'N/A')}")
        print(f"   Type: {bet_data.get('type', 'N/A')}")
        print(f"   Legs: {len(bet_data.get('legs', []))}")
        
        if 'legs' in bet_data and bet_data['legs']:
            first_leg = bet_data['legs'][0]
            print(f"\n   First leg:")
            print(f"      Player: {first_leg.get('player', 'N/A')}")
            print(f"      Team: {first_leg.get('team', 'N/A')}")
            print(f"      Bet Type: {first_leg.get('bet_type', 'N/A')}")
            print(f"      Target: {first_leg.get('target', 'N/A')}")
    
    print("\n✅ Database looks good! Ready to test migration.")
    print("\nTo run the migration:")
    print("   export DATABASE_URL='postgresql://manishslal@localhost/parlays_local'")
    print("   /Users/manishslal/Desktop/Scrapper/.venv/bin/python run_migration.py")

if __name__ == '__main__':
    test_migration()
