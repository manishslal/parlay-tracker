#!/usr/bin/env python3
"""
Remove duplicate live bets
"""
from app import app, db
from models import Bet

def remove_duplicate_bets():
    """Remove duplicate bets with same bet_id"""
    
    with app.app_context():
        # Get all live bets
        live_bets = Bet.query.filter_by(status='live', is_active=True).all()
        
        print(f"📊 Found {len(live_bets)} live bets\n")
        
        # Group by bet_id
        bet_id_groups = {}
        for bet in live_bets:
            bet_data = bet.get_bet_data()
            bet_id = bet_data.get('bet_id', '')
            if bet_id:
                if bet_id not in bet_id_groups:
                    bet_id_groups[bet_id] = []
                bet_id_groups[bet_id].append(bet)
        
        # Find duplicates
        duplicates_removed = 0
        for bet_id, bets in bet_id_groups.items():
            if len(bets) > 1:
                print(f"🔍 Found {len(bets)} copies of bet: {bet_id}")
                bet_data = bets[0].get_bet_data()
                print(f"   Name: {bet_data.get('name')}")
                
                # Keep the first one, delete the rest
                for bet in bets[1:]:
                    print(f"   ❌ Removing duplicate (DB ID: {bet.id})")
                    db.session.delete(bet)
                    duplicates_removed += 1
        
        if duplicates_removed > 0:
            db.session.commit()
            print(f"\n✅ Removed {duplicates_removed} duplicate bets")
        else:
            print("\n✅ No duplicates found")
        
        # Show remaining live bets
        remaining = Bet.query.filter_by(status='live', is_active=True).all()
        print(f"\n📊 Remaining live bets: {len(remaining)}")
        for bet in remaining:
            bet_data = bet.get_bet_data()
            print(f"   - {bet_data.get('name')} (ID: {bet.id})")

if __name__ == '__main__':
    remove_duplicate_bets()
