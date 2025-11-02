#!/usr/bin/env python3
"""
Check which players are missing team/position data in bet 95
"""
from app import app, db
from models import Bet
import json

with app.app_context():
    # Get bet 95 (15 leg SGP+)
    bet = Bet.query.get(95)
    
    if not bet:
        print("❌ Bet 95 not found")
        exit(1)
    
    bet_data = bet.get_bet_data()
    
    print(f"Bet: {bet_data.get('name')}")
    print(f"\nTotal legs: {len(bet_data.get('legs', []))}\n")
    print(f"{'='*80}")
    
    missing_data_players = []
    
    for i, leg in enumerate(bet_data.get('legs', []), 1):
        player = leg.get('player')
        team = leg.get('team')
        position = leg.get('position')
        
        if player and not (team or position):
            missing_data_players.append({
                'leg': i,
                'player': player,
                'stat': leg.get('stat'),
                'away': leg.get('away'),
                'home': leg.get('home')
            })
    
    if missing_data_players:
        print(f"Found {len(missing_data_players)} players missing team/position data:\n")
        for p in missing_data_players:
            print(f"Leg {p['leg']}: {p['player']}")
            print(f"  Stat: {p['stat']}")
            print(f"  Game: {p['away']} @ {p['home']}")
            print()
    else:
        print("✅ All players have team/position data")
    
    print(f"{'='*80}")
