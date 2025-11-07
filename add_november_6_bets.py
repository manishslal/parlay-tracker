#!/usr/bin/env python3
"""
Add three new bets from November 6, 2025:
1. Lamar Jackson SGP (Sunday Nov 9)
2. Tre Tucker/Broncos SGP (Tonight Nov 6)
3. 7-leg parlay (Tonight Nov 6)

All bets for ManishSLal with EToteja as viewer
"""

import os
import sys
from datetime import datetime

# Add parent directory to path to import models
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Bet

def add_bets():
    with app.app_context():
        # Get users
        manish = User.query.filter_by(username='ManishSLal').first()
        etoteja = User.query.filter_by(username='EToteja').first()
        
        if not manish:
            print("ERROR: ManishSLal user not found!")
            return
        if not etoteja:
            print("ERROR: EToteja user not found!")
            return
        
        print(f"Found users - ManishSLal (ID: {manish.id}), EToteja (ID: {etoteja.id})")
        
        # Bet 1: Lamar Jackson SGP - Sunday Nov 9, 2025
        bet1_data = {
            "bet_id": "O/0240915/0000068",
            "name": "Lamar Jackson SGP",
            "type": "Same Game Parlay",
            "wager": "20.00",
            "odds": "+363",
            "returns": "72.70",  # $92.70 payout - $20 wager
            "legs": [
                {
                    "player": "Lamar Jackson",
                    "team": "Baltimore Ravens",
                    "stat": "anytime_touchdown",
                    "target": 1,
                    "away": "Baltimore Ravens",
                    "home": "Minnesota Vikings",
                    "game_date": "2025-11-09"
                },
                {
                    "player": "Lamar Jackson",
                    "team": "Baltimore Ravens",
                    "stat": "rushing_yards",
                    "target": 37.5,
                    "away": "Baltimore Ravens",
                    "home": "Minnesota Vikings",
                    "game_date": "2025-11-09"
                }
            ]
        }
        
        # Bet 2: Tre Tucker/Broncos SGP - Tonight Nov 6, 2025
        bet2_data = {
            "bet_id": "O/1368367/0000044",
            "name": "Tre Tucker/Broncos SGP",
            "type": "Same Game Parlay",
            "wager": "10.00",
            "odds": "+122",
            "returns": "12.24",  # $22.24 payout - $10 wager
            "legs": [
                {
                    "team": "Denver Broncos",
                    "stat": "moneyline",
                    "target": 0,  # Moneyline has no target, just win/loss
                    "away": "Las Vegas Raiders",
                    "home": "Denver Broncos",
                    "game_date": "2025-11-06"
                },
                {
                    "player": "Tre Tucker",
                    "team": "Las Vegas Raiders",
                    "stat": "receiving_yards",
                    "target": 46.5,
                    "away": "Las Vegas Raiders",
                    "home": "Denver Broncos",
                    "game_date": "2025-11-06"
                }
            ]
        }
        
        # Bet 3: 7 Pick Parlay - All legs from Raiders @ Broncos game (tonight)
        # All 7 legs are from the same game: Las Vegas Raiders @ Denver Broncos
        bet3_data = {
            "bet_id": "DK63898069623329495",
            "name": "7 Pick Parlay",
            "type": "Parlay",
            "wager": "10.00",
            "odds": "+442",
            "returns": "44.20",  # $54.20 payout - $10 wager
            "legs": [
                {
                    "player": "Geno Smith",
                    "team": "Las Vegas Raiders",
                    "stat": "passing_yards",
                    "target": 160,
                    "away": "Las Vegas Raiders",
                    "home": "Denver Broncos",
                    "game_date": "2025-11-06"
                },
                {
                    "player": "Bo Nix",
                    "team": "Denver Broncos",
                    "stat": "passing_yards",
                    "target": 170,
                    "away": "Las Vegas Raiders",
                    "home": "Denver Broncos",
                    "game_date": "2025-11-06"
                },
                {
                    "player": "J.K. Dobbins",
                    "team": "Denver Broncos",
                    "stat": "rushing_yards",
                    "target": 50,
                    "away": "Las Vegas Raiders",
                    "home": "Denver Broncos",
                    "game_date": "2025-11-06"
                },
                {
                    "player": "Ashton Jeanty",
                    "team": "Las Vegas Raiders",
                    "stat": "rushing_yards",
                    "target": 40,
                    "away": "Las Vegas Raiders",
                    "home": "Denver Broncos",
                    "game_date": "2025-11-06"
                },
                {
                    "player": "Brock Bowers",
                    "team": "Las Vegas Raiders",
                    "stat": "receiving_yards",
                    "target": 40,
                    "away": "Las Vegas Raiders",
                    "home": "Denver Broncos",
                    "game_date": "2025-11-06"
                },
                {
                    "player": "Tre Tucker",
                    "team": "Las Vegas Raiders",
                    "stat": "receiving_yards",
                    "target": 25,
                    "away": "Las Vegas Raiders",
                    "home": "Denver Broncos",
                    "game_date": "2025-11-06"
                },
                {
                    "player": "Courtland Sutton",
                    "team": "Denver Broncos",
                    "stat": "receiving_yards",
                    "target": 40,
                    "away": "Las Vegas Raiders",
                    "home": "Denver Broncos",
                    "game_date": "2025-11-06"
                }
            ]
        }
        
        print("\n" + "="*80)
        print("BET 1: Lamar Jackson SGP - Sunday Nov 9")
        print("="*80)
        print(f"Bet ID: {bet1_data['bet_id']}")
        print(f"Wager: ${bet1_data['wager']} | Odds: {bet1_data['odds']} | Returns: ${bet1_data['returns']}")
        print(f"Game: {bet1_data['legs'][0]['away']} @ {bet1_data['legs'][0]['home']}")
        print(f"Date: {bet1_data['legs'][0]['game_date']}")
        print("\nLegs:")
        for i, leg in enumerate(bet1_data['legs'], 1):
            print(f"  {i}. {leg['player']} - {leg['stat'].replace('_', ' ').title()}: {leg['target']}")
        
        print("\n" + "="*80)
        print("BET 2: Tre Tucker/Broncos SGP - Tonight Nov 6")
        print("="*80)
        print(f"Bet ID: {bet2_data['bet_id']}")
        print(f"Wager: ${bet2_data['wager']} | Odds: {bet2_data['odds']} | Returns: ${bet2_data['returns']}")
        print(f"Game: {bet2_data['legs'][0]['away']} @ {bet2_data['legs'][0]['home']}")
        print(f"Date: {bet2_data['legs'][0]['game_date']}")
        print("\nLegs:")
        for i, leg in enumerate(bet2_data['legs'], 1):
            if 'player' in leg:
                print(f"  {i}. {leg['player']} - {leg['stat'].replace('_', ' ').title()}: {leg['target']}")
            else:
                print(f"  {i}. {leg['team']} - {leg['stat'].replace('_', ' ').title()}")
        
        print("\n" + "="*80)
        print("BET 3: 7 Pick Parlay - All 7 Legs")
        print("="*80)
        print(f"Bet ID: {bet3_data['bet_id']}")
        print(f"Wager: ${bet3_data['wager']} | Odds: {bet3_data['odds']} | Returns: ${bet3_data['returns']}")
        print(f"Game: {bet3_data['legs'][0]['away']} @ {bet3_data['legs'][0]['home']}")
        print(f"Date: {bet3_data['legs'][0]['game_date']}")
        print("\nAll 7 Legs (Raiders @ Broncos):")
        for i, leg in enumerate(bet3_data['legs'], 1):
            team_abbr = "LV" if leg['team'] == "Las Vegas Raiders" else "DEN"
            print(f"  {i}. {leg['player']} ({team_abbr}) - {leg['stat'].replace('_', ' ').title()}: {leg['target']}")
        
        response = input("\nDo you want to proceed with adding all 3 bets? (y/n): ")
        
        if response.lower() != 'y':
            print("Aborted - no bets added")
            return
        
        # Add Bet 1 - Lamar Jackson SGP (Sunday)
        print("\nAdding Bet 1 (Lamar Jackson SGP)...")
        bet1 = Bet(user_id=manish.id, status='pending', is_active=True)
        bet1.set_bet_data(bet1_data)
        bet1.shared_with.append(etoteja)
        db.session.add(bet1)
        
        # Add Bet 2 - Tre Tucker/Broncos SGP (Tonight)
        print("Adding Bet 2 (Tre Tucker/Broncos SGP)...")
        bet2 = Bet(user_id=manish.id, status='pending', is_active=True)
        bet2.set_bet_data(bet2_data)
        bet2.shared_with.append(etoteja)
        db.session.add(bet2)
        
        # Add Bet 3 - 7 Pick Parlay (Tonight - all 7 legs)
        print("Adding Bet 3 (7 Pick Parlay - all 7 legs)...")
        bet3 = Bet(user_id=manish.id, status='pending', is_active=True)
        bet3.set_bet_data(bet3_data)
        bet3.shared_with.append(etoteja)
        db.session.add(bet3)
        
        db.session.commit()
        
        print("\n✅ Successfully added 3 bets!")
        print(f"   - Bet 1 (Lamar Jackson SGP) ID: {bet1.id}")
        print(f"   - Bet 2 (Tre Tucker/Broncos SGP) ID: {bet2.id}")
        print(f"   - Bet 3 (7 Pick Parlay) ID: {bet3.id}")
        print("\nAll bets added successfully with all legs from Raiders @ Broncos game!")

if __name__ == '__main__':
    add_bets()
