#!/usr/bin/env python3
"""
Debug script to see what's actually in the database vs backup
"""
import json
from app import app, db
from models import Bet

def debug_restore():
    """Debug the restore process step by step"""
    
    print("🔍 DEBUGGING ESPN DATA RESTORATION\n")
    
    # Load backup
    backup_file = 'data/backup_20251101_110041/Historical_Bets.json'
    print(f"📁 Loading backup: {backup_file}")
    with open(backup_file, 'r') as f:
        backup_data = json.load(f)
    print(f"✅ Backup has {len(backup_data)} bets\n")
    
    with app.app_context():
        # Get a few bets that should have been updated
        problem_bets = [
            'TNF SGP',
            '4 Picks (All-In) SGP',
            '9 Pick ML Parlay - Week 8'
        ]
        
        for bet_name in problem_bets:
            print(f"\n{'='*60}")
            print(f"🔍 Checking: {bet_name}")
            print('='*60)
            
            # Find in backup
            backup_bet = None
            for b in backup_data:
                if b.get('name') == bet_name:
                    backup_bet = b
                    break
            
            if backup_bet:
                print(f"\n✅ Found in backup")
                print(f"   Legs in backup: {len(backup_bet.get('legs', []))}")
                
                # Check first leg data
                if backup_bet.get('legs'):
                    first_leg = backup_bet['legs'][0]
                    print(f"\n   First leg from backup:")
                    print(f"     Player: {first_leg.get('player', 'N/A')}")
                    print(f"     Line: {first_leg.get('line', 'N/A')}")
                    print(f"     Market: {first_leg.get('market', 'N/A')}")
                    print(f"     Current: {first_leg.get('current', 'MISSING')}")
                    print(f"     Status: {first_leg.get('status', 'MISSING')}")
                    print(f"     Result: {first_leg.get('result', 'MISSING')}")
            else:
                print(f"\n❌ NOT found in backup")
                continue
            
            # Find in database
            db_bets = Bet.query.filter_by(status='completed').all()
            db_bet = None
            for b in db_bets:
                bet_data = b.get_bet_data()
                if bet_data.get('name') == bet_name:
                    db_bet = b
                    break
            
            if db_bet:
                bet_data = db_bet.get_bet_data()
                print(f"\n✅ Found in database")
                print(f"   Bet ID: {db_bet.id}")
                print(f"   API Fetched: {db_bet.api_fetched}")
                print(f"   Legs in database: {len(bet_data.get('legs', []))}")
                
                # Check first leg data
                if bet_data.get('legs'):
                    first_leg = bet_data['legs'][0]
                    print(f"\n   First leg from database:")
                    print(f"     Player: {first_leg.get('player', 'N/A')}")
                    print(f"     Line: {first_leg.get('line', 'N/A')}")
                    print(f"     Market: {first_leg.get('market', 'N/A')}")
                    print(f"     Current: {first_leg.get('current', 'MISSING')}")
                    print(f"     Status: {first_leg.get('status', 'MISSING')}")
                    print(f"     Result: {first_leg.get('result', 'MISSING')}")
                    
                    # Check if it has ESPN data
                    has_data = 'current' in first_leg and first_leg.get('current') is not None
                    print(f"\n   Has ESPN data: {'✅ YES' if has_data else '❌ NO'}")
            else:
                print(f"\n❌ NOT found in database")

if __name__ == '__main__':
    debug_restore()
