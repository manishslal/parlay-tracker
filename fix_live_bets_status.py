#!/usr/bin/env python3
"""
Fix the two live bets: update status and game dates
"""
from app import app, db
from models import Bet

def fix_live_bets():
    """Fix status and dates for the two new bets"""
    
    with app.app_context():
        # Get the two pending bets
        pending_bets = Bet.query.filter_by(status='pending', is_active=True).all()
        
        print(f"📊 Found {len(pending_bets)} pending bets\n")
        
        for bet in pending_bets:
            bet_data = bet.get_bet_data()
            print(f"{'='*70}")
            print(f"Bet: {bet_data.get('name')}")
            print(f"Current status: {bet.status}")
            print('='*70)
            
            # Update status to 'live'
            bet.status = 'live'
            
            # Update game_date to today (2025-11-02) for all legs except Monday
            updated_legs = 0
            for leg in bet_data.get('legs', []):
                old_date = leg.get('game_date')
                if old_date == '2025-11-03':
                    leg['game_date'] = '2025-11-02'
                    updated_legs += 1
                    print(f"  ✅ Updated leg date: {old_date} → 2025-11-02")
            
            # Save updated bet data
            bet.set_bet_data(bet_data, preserve_status=True)
            bet.status = 'live'  # Set again after set_bet_data
            
            print(f"  ✅ Status updated: pending → live")
            print(f"  ✅ Updated {updated_legs} leg dates")
        
        if pending_bets:
            db.session.commit()
            print(f"\n✅ Updated {len(pending_bets)} bets")
            
            # Verify
            print("\n📊 Verifying live bets:")
            live_bets = Bet.query.filter_by(status='live', is_active=True).all()
            print(f"  Total live bets: {len(live_bets)}")
            for bet in live_bets:
                bet_data = bet.get_bet_data()
                dates = set()
                for leg in bet_data.get('legs', []):
                    dates.add(leg.get('game_date'))
                print(f"    - {bet_data.get('name')} | Dates: {', '.join(sorted(dates))}")
        else:
            print("\n✅ No pending bets to fix")

if __name__ == '__main__':
    fix_live_bets()
