#!/usr/bin/env python3
"""
Fix the payout for bet O/0240915/0000065 from $5769.00 to $57.69
"""
from app import app, db
from models import Bet

def fix_payout():
    """Fix incorrect payout for bet 65"""
    
    with app.app_context():
        # Find the specific bet
        bet = Bet.query.filter(Bet.bet_data.cast(db.String).like('%O/0240915/0000065%')).first()
        
        if not bet:
            print("❌ Bet O/0240915/0000065 not found")
            return
        
        bet_data = bet.get_bet_data()
        
        print(f"Found bet: {bet_data.get('name')}")
        print(f"Current payout: ${bet_data.get('potential_payout', 0):.2f}")
        
        # Fix the payout
        bet_data['potential_payout'] = 57.69
        
        # Save
        bet.set_bet_data(bet_data, preserve_status=True)
        bet.status = 'live'  # Preserve status
        
        db.session.commit()
        
        print(f"✅ Updated payout to: $57.69")

if __name__ == '__main__':
    fix_payout()
