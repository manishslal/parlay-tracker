#!/usr/bin/env python3
"""
Add Kyren Williams + Puka Nacua 3-Leg SGP for jtahiliani
=========================================================
This script adds a live bet from the Saints @ Rams game (Nov 2, 2025)

Bet Details:
- 3-leg Same Game Parlay (SGP)
- $20 wager → $79.40 payout (+297 odds with 50% boost)
- Legs: Kyren TD, Kyren 70+ rush yds, Puka 90+ rec yds
"""

import os
import sys
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Bet

def add_bet_for_jtahiliani():
    """Add the 3-leg SGP bet for jtahiliani"""
    
    with app.app_context():
        print("\n" + "="*60)
        print("ADD BET FOR JTAHILIANI")
        print("="*60)
        
        # Find jtahiliani user
        user = User.query.filter_by(username='jtahiliani').first()
        
        if not user:
            print("\n❌ ERROR: User 'jtahiliani' not found!")
            print("Please run migrate_to_shared_bets.py first to create the user.")
            return
        
        print(f"\n✅ Found user: {user.username} (ID: {user.id})")
        
        # Bet data structure
        bet_data = {
            "name": "3 Pick Parlay",
            "type": "SGP",
            "odds": "+297",
            "wager": 20.0,
            "returns": 79.40,
            "betting_site": "FanDuel",
            "bet_id": None,
            "boost": "+50% Parlay Boost",
            "legs": [
                {
                    "game_date": "2025-11-02",
                    "away": "New Orleans Saints",
                    "home": "Los Angeles Rams",
                    "player": "Kyren Williams",
                    "target": 1,
                    "stat": "anytime_touchdown",
                    "stat_add": None,
                    "team": "Los Angeles Rams",
                    "position": "RB"
                },
                {
                    "game_date": "2025-11-02",
                    "away": "New Orleans Saints",
                    "home": "Los Angeles Rams",
                    "player": "Kyren Williams",
                    "target": 70,
                    "stat": "rushing_yards",
                    "stat_add": "over",
                    "team": "Los Angeles Rams",
                    "position": "RB"
                },
                {
                    "game_date": "2025-11-02",
                    "away": "New Orleans Saints",
                    "home": "Los Angeles Rams",
                    "player": "Puka Nacua",
                    "target": 90,
                    "stat": "receiving_yards",
                    "stat_add": "over",
                    "team": "Los Angeles Rams",
                    "position": "WR"
                }
            ],
            "bet_date": "2025-11-02",
            "sport": "NFL",
            "status": "live"
        }
        
        print("\n" + "="*60)
        print("BET DETAILS")
        print("="*60)
        print(f"Name: {bet_data['name']}")
        print(f"Type: {bet_data['type']}")
        print(f"Wager: ${bet_data['wager']}")
        print(f"To Pay: ${bet_data['returns']}")
        print(f"Odds: {bet_data['odds']}")
        print(f"Boost: {bet_data['boost']}")
        print(f"Site: {bet_data['betting_site']}")
        print(f"Status: {bet_data['status']}")
        print(f"\nLegs ({len(bet_data['legs'])}):")
        for i, leg in enumerate(bet_data['legs'], 1):
            print(f"  {i}. {leg['player']} - {leg['stat'].replace('_', ' ').title()} {leg['target']}")
            if leg['stat_add']:
                print(f"     ({leg['stat_add']})")
        
        # Create bet
        try:
            bet = Bet(user_id=user.id)
            bet.status = 'live'  # Live bet currently in progress
            bet.is_active = True  # Active (not in historical)
            bet.bet_type = 'SGP'
            bet.betting_site = 'FanDuel'
            bet.bet_date = '2025-11-02'
            bet.api_fetched = 'No'  # Will fetch live data
            bet.set_bet_data(bet_data)
            
            db.session.add(bet)
            db.session.commit()
            
            print("\n" + "="*60)
            print("✅ SUCCESS!")
            print("="*60)
            print(f"Bet ID: {bet.id}")
            print(f"User: {user.username}")
            print(f"Status: {bet.status}")
            print(f"Active: {bet.is_active}")
            print(f"\nThe bet is now live and will fetch real-time stats from ESPN!")
            print(f"\nView it at: http://localhost:5000/live (or on Render)")
            
        except Exception as e:
            print("\n" + "="*60)
            print("❌ ERROR CREATING BET")
            print("="*60)
            print(f"Error: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    add_bet_for_jtahiliani()
