#!/usr/bin/env python3
"""
Update Cam Ward's team from Miami Dolphins to Tennessee Titans
"""
from app import app, db
from models import Bet

def update_cam_ward():
    """Update Cam Ward's team"""
    
    with app.app_context():
        bet = Bet.query.get(95)
        
        if not bet:
            print("❌ Bet 95 not found")
            return
        
        bet_data = bet.get_bet_data()
        
        print(f"Bet: {bet_data.get('name')}\n")
        print("="*80)
        
        updated = False
        
        for i, leg in enumerate(bet_data.get('legs', []), 1):
            if leg.get('player') == 'Cam Ward':
                print(f"Leg {i}: Cam Ward")
                print(f"  Current team: {leg.get('team')}")
                
                leg['team'] = 'Tennessee Titans'
                
                print(f"  Updated team: {leg['team']}")
                print()
                updated = True
                break
        
        if updated:
            bet.set_bet_data(bet_data, preserve_status=True)
            db.session.commit()
            
            print("="*80)
            print("✅ Updated Cam Ward's team to Tennessee Titans")
        else:
            print("="*80)
            print("⚠️  Cam Ward not found in bet")
        
        print("="*80)

if __name__ == '__main__':
    print("="*80)
    print("UPDATING CAM WARD'S TEAM")
    print("="*80 + "\n")
    update_cam_ward()
