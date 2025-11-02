#!/usr/bin/env python3
"""
Fix Cowboys game date to 2025-11-03
"""
from app import app, db
from models import Bet

def fix_cowboys_date():
    """Update Cowboys game from 11-04 to 11-03"""
    
    with app.app_context():
        # Get live bets
        live_bets = Bet.query.filter_by(status='live', is_active=True).all()
        
        print(f"📊 Found {len(live_bets)} live bets\n")
        
        updated_count = 0
        
        for bet in live_bets:
            bet_data = bet.get_bet_data()
            updated = False
            
            # Find Cowboys game legs
            for leg in bet_data.get('legs', []):
                if leg.get('home') == 'Dallas Cowboys' and leg.get('game_date') == '2025-11-04':
                    print(f"  🔧 Fixing Cowboys game in: {bet_data.get('name')}")
                    print(f"     Old date: {leg.get('game_date')}")
                    leg['game_date'] = '2025-11-03'
                    print(f"     New date: 2025-11-03")
                    updated = True
            
            if updated:
                bet.set_bet_data(bet_data, preserve_status=True)
                bet.status = 'live'  # Preserve status
                updated_count += 1
        
        if updated_count > 0:
            db.session.commit()
            print(f"\n✅ Updated {updated_count} bets")
        else:
            print("\n✅ No Cowboys games found with wrong date")

if __name__ == '__main__':
    fix_cowboys_date()
