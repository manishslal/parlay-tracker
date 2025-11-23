#!/usr/bin/env python3
"""
Check the actual away_team and home_team values in the database for bets 158-160.
"""

import sys
import os
sys.path.append('/Users/manishslal/Desktop/Scrapper')

from dotenv import load_dotenv
load_dotenv()

from app import app, db
from models import BetLeg

with app.app_context():
    bet_ids = [158, 159, 160]
    
    for bet_id in bet_ids:
        legs = db.session.query(BetLeg).filter(BetLeg.bet_id == bet_id).all()
        print(f"\nBet {bet_id}:")
        for leg in legs:
            print(f"  Leg {leg.id}: home='{leg.home_team}' away='{leg.away_team}' player='{leg.player_name}'")
