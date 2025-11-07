#!/usr/bin/env python3
"""
Update November 6 bets with missing bet_date and betting_site fields
Run this on Render to fix existing bets in production database
"""

import os
import sys

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Bet

def update_november_6_bets():
    """Update the 3 November 6 bets with bet_date and betting_site fields"""
    
    with app.app_context():
        print("=" * 60)
        print("UPDATING NOVEMBER 6 BETS")
        print("=" * 60)
        
        # Find ManishSLal user (case-insensitive)
        manish = User.query.filter(db.func.lower(User.username) == 'manishslal').first()
        if not manish:
            print("ERROR: ManishSLal user not found!")
            return False
        
        print(f"\nFound user: {manish.username} (ID: {manish.id})")
        
        # Get all bets for this user
        all_bets = Bet.query.filter_by(user_id=manish.id).all()
        print(f"Total bets for user: {len(all_bets)}")
        
        # Define the updates for each bet by bet_id
        updates = {
            "O/0240915/0000068": {
                "name": "Lamar Jackson SGP",
                "betting_site": "FanDuel",
                "bet_date": "2025-11-09"
            },
            "O/1368367/0000044": {
                "name": "Tre Tucker/Broncos SGP",
                "betting_site": "FanDuel",
                "bet_date": "2025-11-06"
            },
            "DK63898069623329495": {
                "name": "7 Pick Parlay",
                "betting_site": "DraftKings",
                "bet_date": "2025-11-06"
            }
        }
        
        updated_count = 0
        
        for bet in all_bets:
            bet_data = bet.get_bet_data()
            bet_id = bet_data.get('bet_id')
            
            # Check if this is one of the November 6 bets
            if bet_id in updates:
                update_info = updates[bet_id]
                
                print(f"\n{'='*60}")
                print(f"Updating bet: {update_info['name']}")
                print(f"Bet ID: {bet_id}")
                
                # Check if fields are already set
                has_betting_site = bet_data.get('betting_site') is not None
                has_bet_date = bet_data.get('bet_date') is not None
                
                print(f"Current state:")
                print(f"  - betting_site: {bet_data.get('betting_site', 'MISSING')}")
                print(f"  - bet_date: {bet_data.get('bet_date', 'MISSING')}")
                
                # Update the fields
                changes_made = False
                
                if not has_betting_site:
                    bet_data['betting_site'] = update_info['betting_site']
                    changes_made = True
                    print(f"  ✓ Added betting_site: {update_info['betting_site']}")
                
                if not has_bet_date:
                    bet_data['bet_date'] = update_info['bet_date']
                    changes_made = True
                    print(f"  ✓ Added bet_date: {update_info['bet_date']}")
                
                if changes_made:
                    # Save back to database
                    bet.set_bet_data(bet_data, preserve_status=True)
                    updated_count += 1
                    print(f"  ✓ Bet updated successfully!")
                else:
                    print(f"  ℹ No updates needed - fields already set")
        
        # Commit all changes
        if updated_count > 0:
            try:
                db.session.commit()
                print(f"\n{'='*60}")
                print(f"✅ SUCCESS: Updated {updated_count} bet(s)")
                print(f"{'='*60}")
                return True
            except Exception as e:
                db.session.rollback()
                print(f"\n{'='*60}")
                print(f"❌ ERROR: Failed to commit changes: {e}")
                print(f"{'='*60}")
                return False
        else:
            print(f"\n{'='*60}")
            print(f"ℹ No bets needed updating - all fields already set")
            print(f"{'='*60}")
            return True

if __name__ == '__main__':
    success = update_november_6_bets()
    sys.exit(0 if success else 1)
