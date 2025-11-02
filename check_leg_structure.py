#!/usr/bin/env python3
"""
Check the exact structure of the total_points leg
"""
from app import app, db
from models import Bet
import json

with app.app_context():
    # Get bet 94 (7 leg parlay)
    bet = Bet.query.get(94)
    
    if not bet:
        print("❌ Bet 94 not found")
        exit(1)
    
    bet_data = bet.get_bet_data()
    
    print(f"Bet: {bet_data.get('name')}")
    print(f"\nTotal legs: {len(bet_data.get('legs', []))}\n")
    
    for i, leg in enumerate(bet_data.get('legs', []), 1):
        print(f"{'='*80}")
        print(f"LEG {i}:")
        print(f"{'='*80}")
        print(json.dumps(leg, indent=2))
        print()
        
        # Check for total_points leg
        stat = leg.get('stat', '')
        if 'total' in stat.lower():
            print("⚠️  THIS IS THE TOTAL POINTS LEG")
            print(f"   stat: {leg.get('stat')}")
            print(f"   away: {leg.get('away')}")
            print(f"   home: {leg.get('home')}")
            print(f"   player: {leg.get('player')}")
            print(f"   team: {leg.get('team')}")
            print(f"   over_under: {leg.get('over_under')}")
            print(f"   stat_add: {leg.get('stat_add')}")
            print()
