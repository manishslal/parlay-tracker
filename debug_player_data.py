#!/usr/bin/env python3
"""
Debug: Check exact player data for the 4 players
"""
from app import app, db
from models import Bet
import json

with app.app_context():
    bet = Bet.query.get(95)
    
    if not bet:
        print("❌ Bet 95 not found")
        exit(1)
    
    bet_data = bet.get_bet_data()
    
    print(f"Bet: {bet_data.get('name')}\n")
    print("="*80)
    
    target_players = ['Bryce Young', 'Jaxson Dart', 'Cam Ward', 'C.J. Stroud']
    
    for i, leg in enumerate(bet_data.get('legs', []), 1):
        player = leg.get('player')
        
        if player in target_players:
            print(f"\nLeg {i}: {player}")
            print(f"  Full leg data:")
            print(json.dumps(leg, indent=4))
            print()
    
    print("="*80)
