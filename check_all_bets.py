#!/usr/bin/env python3
"""
Check all bets in database and remove duplicates
"""
from app import app, db
from models import Bet

def check_all_bets():
    """Show all bets in database"""
    
    with app.app_context():
        # Get ALL bets
        all_bets = Bet.query.all()
        
        print(f"📊 TOTAL BETS IN DATABASE: {len(all_bets)}\n")
        
        # Group by status
        by_status = {}
        for bet in all_bets:
            status = bet.status
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(bet)
        
        for status, bets in by_status.items():
            print(f"\n{status.upper()}: {len(bets)} bets")
            print("-" * 50)
            for bet in bets:
                bet_data = bet.get_bet_data()
                print(f"  ID: {bet.id} | is_active: {bet.is_active} | {bet_data.get('name')} | bet_id: {bet_data.get('bet_id')}")
        
        # Check for duplicates
        print(f"\n\n{'='*70}")
        print("CHECKING FOR DUPLICATES")
        print('='*70)
        
        bet_id_map = {}
        for bet in all_bets:
            bet_data = bet.get_bet_data()
            bet_id = bet_data.get('bet_id', '')
            if bet_id:
                if bet_id not in bet_id_map:
                    bet_id_map[bet_id] = []
                bet_id_map[bet_id].append(bet)
        
        duplicates_found = 0
        for bet_id, bets in bet_id_map.items():
            if len(bets) > 1:
                duplicates_found += 1
                print(f"\n🔍 Duplicate bet_id: {bet_id}")
                print(f"   Found {len(bets)} copies:")
                for bet in bets:
                    bet_data = bet.get_bet_data()
                    print(f"     - DB ID: {bet.id} | Status: {bet.status} | is_active: {bet.is_active} | {bet_data.get('name')}")
        
        if duplicates_found == 0:
            print("\n✅ No duplicates found!")
        else:
            print(f"\n❌ Found {duplicates_found} sets of duplicates")
            print("\nTo remove duplicates, I'll keep the first occurrence of each bet_id")
            
            response = input("\nRemove duplicates? (yes/no): ")
            if response.lower() == 'yes':
                removed = 0
                for bet_id, bets in bet_id_map.items():
                    if len(bets) > 1:
                        # Keep first, delete rest
                        for bet in bets[1:]:
                            print(f"  ❌ Removing duplicate DB ID: {bet.id}")
                            db.session.delete(bet)
                            removed += 1
                
                db.session.commit()
                print(f"\n✅ Removed {removed} duplicate bets")

if __name__ == '__main__':
    check_all_bets()
