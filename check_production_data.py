#!/usr/bin/env python3
"""
Check production database to see how many bets have ESPN data
"""
import json
from app import app, db
from models import Bet

def check_espn_data():
    """Check all completed bets for ESPN data"""
    
    with app.app_context():
        completed_bets = Bet.query.filter_by(status='completed').all()
        
        print(f"📊 Total completed bets: {len(completed_bets)}\n")
        
        bets_with_data = []
        bets_without_data = []
        
        for db_bet in completed_bets:
            bet_data = db_bet.get_bet_data()
            bet_name = bet_data.get('name', 'Unnamed')
            
            # Check if bet has ESPN data
            has_espn_data = False
            for leg in bet_data.get('legs', []):
                if 'current' in leg and leg.get('current') is not None:
                    has_espn_data = True
                    break
            
            if has_espn_data:
                bets_with_data.append(bet_name)
            else:
                bets_without_data.append(bet_name)
        
        print(f"✅ Bets WITH ESPN data: {len(bets_with_data)} ({len(bets_with_data)/len(completed_bets)*100:.1f}%)")
        print(f"❌ Bets WITHOUT ESPN data: {len(bets_without_data)} ({len(bets_without_data)/len(completed_bets)*100:.1f}%)")
        
        if bets_without_data:
            print(f"\n❌ Bets still missing ESPN data:")
            for i, name in enumerate(bets_without_data, 1):
                print(f"  {i}. {name}")
        
        if len(bets_without_data) == 0:
            print("\n🎉 ALL HISTORICAL BETS HAVE ESPN DATA! 🎉")
        elif len(bets_without_data) <= 1:
            print(f"\n✨ Almost perfect! Only {len(bets_without_data)} bet missing data.")
        
        return len(bets_with_data), len(bets_without_data)

if __name__ == '__main__':
    check_espn_data()
