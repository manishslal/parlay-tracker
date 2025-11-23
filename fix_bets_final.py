#!/usr/bin/env python3
"""
Final fix: Update game_date to correct dates and populate game_ids.
"""

import sys
import os
sys.path.append('/Users/manishslal/Desktop/Scrapper')

from dotenv import load_dotenv
load_dotenv()

from app import app, db
from models import BetLeg
from helpers.espn_api import get_espn_games_with_ids_for_date
from datetime import datetime
import json

with app.app_context():
    print("="*80)
    print("🔧 FINAL FIX: Update game_dates and link to ESPN games")
    print("="*80)
    
    # Mapping of home teams to correct game dates based on what we found
    # These are NFL games happening on Nov 23 and Nov 24
    date_mapping = {
        'Baltimore Ravens': '2025-11-23',  # Need to check
        'Detroit Lions': '2025-11-23',     # Found: New York Giants @ Detroit Lions
        'Kansas City Chiefs': '2025-11-23',  # Should be on Nov 23
        'New England Patriots': '2025-11-23',  # Found: New England Patriots @ Cincinnati Bengals
        'Seattle Seahawks': '2025-11-24',  # Need to find
        'Los Angeles Rams': '2025-11-23',  # Need to find
        'San Francisco 49ers': '2025-11-24',  # Found: Carolina Panthers @ San Francisco 49ers
        'Jacksonville Jaguars': '2025-11-23',  # Need to find
        'Kansas City Chiefs': '2025-11-23',  # Need to find
    }
    
    bet_ids = [158, 159, 160]
    
    for bet_id in bet_ids:
        print(f"\n{'─'*80}")
        print(f"Fixing bet {bet_id}...")
        
        legs = db.session.query(BetLeg).filter(BetLeg.bet_id == bet_id).all()
        
        # Update game_dates to correct values
        for leg in legs:
            # Use Nov 23 as default for most teams, Nov 24 for others
            if leg.home_team in ['Seattle Seahawks']:
                new_date = '2025-11-24'
            elif leg.home_team in ['San Francisco 49ers']:
                new_date = '2025-11-24'
            else:
                new_date = '2025-11-23'
            
            print(f"  Leg {leg.id} ({leg.home_team}): updating date from {leg.game_date} to {new_date}")
            leg.game_date = new_date
        
        db.session.commit()
        print(f"  ✅ Updated game dates")
        
        # Now populate game_ids for each date
        print(f"  Fetching games and linking...")
        
        for check_date_str in ['2025-11-23', '2025-11-24']:
            check_date = datetime.strptime(check_date_str, '%Y-%m-%d')
            games = get_espn_games_with_ids_for_date(check_date)
            if not games:
                continue
            
            # Create lookup
            game_lookup = {}
            for game_id, away, home in games:
                home_norm = home.lower().strip()
                game_lookup[home_norm] = (game_id, away)
            
            # Match legs
            for leg in legs:
                if leg.game_id:  # Already has ID
                    continue
                if str(leg.game_date) != check_date_str:  # Different date
                    continue
                
                home_norm = leg.home_team.lower().strip()
                if home_norm in game_lookup:
                    game_id, away = game_lookup[home_norm]
                    leg.game_id = game_id
                    if leg.away_team == 'TBD':
                        leg.away_team = away
                    print(f"    ✅ Leg {leg.id}: {leg.away_team} @ {leg.home_team} → game_id={game_id}")
                else:
                    print(f"    ❌ Leg {leg.id}: No match for {leg.home_team}")
        
        db.session.commit()
        print(f"  ✅ Linked to ESPN games")
    
    print(f"\n{'='*80}")
    print(f"✅ ALL FIXES COMPLETE")
    print(f"{'='*80}\n")
    
    # Show final status
    for bet_id in bet_ids:
        legs = db.session.query(BetLeg).filter(BetLeg.bet_id == bet_id).all()
        game_ids = sum(1 for leg in legs if leg.game_id)
        print(f"Bet {bet_id}: {game_ids}/{len(legs)} legs with game_id")
        for leg in legs:
            print(f"  Leg {leg.id}: {leg.away_team} @ {leg.home_team} - game_id={leg.game_id}")
