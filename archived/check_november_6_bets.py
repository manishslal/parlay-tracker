#!/usr/bin/env python3
"""
Check what November 6 bets exist in the database
"""

import os
import sys

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Bet

def check_november_6_bets():
    """Check for November 6 bets and their current state"""
    
    with app.app_context():
        print("=" * 80)
        print("CHECKING NOVEMBER 6 BETS")
        print("=" * 80)
        
        # Find ManishSLal user (case-insensitive)
        manish = User.query.filter(db.func.lower(User.username) == 'manishslal').first()
        if not manish:
            print("ERROR: ManishSLal user not found!")
            return
        
        print(f"\nUser: {manish.username} (ID: {manish.id})")
        
        # Get all bets for this user
        all_bets = Bet.query.filter_by(user_id=manish.id).all()
        print(f"Total bets: {len(all_bets)}")
        
        # Look for November 6 related bets
        target_names = ["Lamar Jackson SGP", "Tre Tucker/Broncos SGP", "7 Pick Parlay"]
        target_bet_ids = ["O/0240915/0000068", "O/1368367/0000044", "DK63898069623329495"]
        
        print(f"\n{'='*80}")
        print("LOOKING FOR TARGET BETS:")
        for name in target_names:
            print(f"  - {name}")
        
        found_bets = []
        
        for bet in all_bets:
            bet_data = bet.get_bet_data()
            bet_name = bet_data.get('name', '')
            bet_id = bet_data.get('bet_id', '')
            
            # Check if this matches any of our target bets
            if bet_name in target_names or bet_id in target_bet_ids:
                found_bets.append(bet)
        
        print(f"\n{'='*80}")
        print(f"FOUND {len(found_bets)} MATCHING BET(S):")
        print(f"{'='*80}")
        
        for i, bet in enumerate(found_bets, 1):
            bet_data = bet.get_bet_data()
            print(f"\n--- Bet {i} (DB ID: {bet.id}) ---")
            print(f"Name: {bet_data.get('name', 'N/A')}")
            print(f"Bet ID: {bet_data.get('bet_id', 'N/A')}")
            print(f"Type: {bet_data.get('type', 'N/A')}")
            print(f"Betting Site: {bet_data.get('betting_site', 'MISSING ❌')}")
            print(f"Bet Date: {bet_data.get('bet_date', 'MISSING ❌')}")
            print(f"Wager: ${bet_data.get('wager', 'N/A')}")
            print(f"Odds: {bet_data.get('odds', 'N/A')}")
            print(f"Status: {bet.status}")
            print(f"Active: {bet.is_active}")
            print(f"Number of legs: {len(bet_data.get('legs', []))}")
        
        if len(found_bets) == 0:
            print("\n⚠️  WARNING: No matching bets found!")
            print("This means the bets either:")
            print("  1. Haven't been added yet")
            print("  2. Have different names/IDs than expected")
            print("  3. Are in production but not in local database")

if __name__ == '__main__':
    check_november_6_bets()
