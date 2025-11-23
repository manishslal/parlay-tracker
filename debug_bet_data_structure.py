#!/usr/bin/env python3
"""
Debug script to check the actual data being passed for bets 158, 159, 160
and understand why population functions might have failed.
"""

import sys
import os
sys.path.append('/Users/manishslal/Desktop/Scrapper')

from dotenv import load_dotenv
load_dotenv()

from app import app, db
from models import Bet, BetLeg
import json

def analyze_bet_data():
    """Check the raw bet_data JSON for bets 158, 159, 160."""
    
    with app.app_context():
        bet_ids = [158, 159, 160]
        
        for bet_id in bet_ids:
            bet = Bet.query.get(bet_id)
            
            if not bet:
                print(f"❌ Bet {bet_id} not found!")
                continue
            
            print(f"\n{'='*80}")
            print(f"BET {bet_id} - BET_DATA STRUCTURE")
            print(f"{'='*80}")
            
            if bet.bet_data:
                try:
                    bet_data = json.loads(bet.bet_data)
                    print(json.dumps(bet_data, indent=2)[:2000])  # Show first 2000 chars
                except Exception as e:
                    print(f"Error parsing: {e}")
            else:
                print("No bet_data stored")
            
            print(f"\nBET INFORMATION IN TABLE:")
            print(f"  betting_site_id: {bet.betting_site_id}")
            print(f"  betting_site: {bet.betting_site}")
            print(f"  bet_type: {bet.bet_type}")
            print(f"  bet_date: {bet.bet_date}")
            print(f"  created_at: {bet.created_at}")

if __name__ == '__main__':
    analyze_bet_data()
