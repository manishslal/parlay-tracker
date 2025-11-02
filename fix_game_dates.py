#!/usr/bin/env python3
"""
Update game dates in existing live bets to today
"""
from app import app, db
from models import Bet

def fix_game_dates():
    """Update all game_date fields from 2025-11-03 to 2025-11-02"""
    
    with app.app_context():
        # Get all live bets
        live_bets = Bet.query.filter_by(status='live', is_active=True).all()
        
        print(f"📊 Found {len(live_bets)} live bets\n")
        
        updated_count = 0
        
        for bet in live_bets:
            bet_data = bet.get_bet_data()
            updated = False
            
            # Update game_date in all legs (except Monday game)
            for leg in bet_data.get('legs', []):
                if leg.get('game_date') == '2025-11-03':
                    leg['game_date'] = '2025-11-02'
                    updated = True
            
            if updated:
                bet.set_bet_data(bet_data, preserve_status=True)
                updated_count += 1
                print(f"✅ Updated: {bet_data.get('name')}")
        
        if updated_count > 0:
            db.session.commit()
            print(f"\n✅ Updated {updated_count} bets to today's date (2025-11-02)")
        else:
            print("\n✅ No bets needed updating")
        
        # Show current dates
        print("\n📅 Current game dates in live bets:")
        live_bets = Bet.query.filter_by(status='live', is_active=True).all()
        for bet in live_bets:
            bet_data = bet.get_bet_data()
            dates = set()
            for leg in bet_data.get('legs', []):
                dates.add(leg.get('game_date'))
            print(f"  {bet_data.get('name')}: {', '.join(sorted(dates))}")

if __name__ == '__main__':
    fix_game_dates()
