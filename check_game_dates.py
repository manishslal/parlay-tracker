#!/usr/bin/env python3
"""
Check what dates have NFL games and find the right game date for these bets.
"""

import sys
import os
sys.path.append('/Users/manishslal/Desktop/Scrapper')

from dotenv import load_dotenv
load_dotenv()

from app import app, db
from models import BetLeg
from helpers.espn_api import get_espn_games_with_ids_for_date
from datetime import datetime, timedelta

with app.app_context():
    # Check the sport and game_date for bets
    legs = db.session.query(BetLeg).filter(BetLeg.bet_id.in_([158, 159, 160])).all()
    
    print("Bet legs info:")
    for leg in legs[:1]:
        print(f"  Sport: {leg.sport}")
        print(f"  Game Date: {leg.game_date}")
        print(f"  Home Team: {leg.home_team}")
    
    # Try fetching NFL games for the game_date and nearby dates
    game_date = legs[0].game_date if legs else None
    
    if game_date:
        print(f"\nSearching for NFL games around {game_date}...")
        
        # Try this date and +/- 2 days
        for delta in [-2, -1, 0, 1, 2]:
            check_date = game_date + timedelta(days=delta)
            print(f"\n  Checking {check_date}...")
            games = get_espn_games_with_ids_for_date(check_date)
            
            if games:
                print(f"    Total games: {len(games)}")
                # Show first few
                for game_id, away, home in games[:3]:
                    print(f"      {away} @ {home} (ID: {game_id})")
            else:
                print(f"    No games found")
