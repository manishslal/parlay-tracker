#!/usr/bin/env python3
"""
Manual fix script for bets 158-160 with direct game_id matching.
This script will:
1. Fix the betting_site and bet_type fields
2. Manually look up and populate game_ids
3. Handle the session/player errors
"""

import sys
import os
sys.path.append('/Users/manishslal/Desktop/Scrapper')

from dotenv import load_dotenv
load_dotenv()

from app import app, db, populate_game_ids_for_bet
from models import Bet, BetLeg
from helpers.espn_api import get_espn_games_with_ids_for_date
import json
from datetime import datetime

def fix_bets_158_160():
    """Manually fix bets 158, 159, 160."""
    
    with app.app_context():
        bet_ids = [158, 159, 160]
        
        for bet_id in bet_ids:
            print(f"\n{'='*80}")
            print(f"🔧 FIXING BET {bet_id}")
            print(f"{'='*80}")
            
            bet = Bet.query.get(bet_id)
            if not bet:
                print(f"❌ Bet {bet_id} not found!")
                continue
            
            # Show before state
            print(f"\n📋 BEFORE FIX:")
            print(f"  betting_site: {bet.betting_site}")
            print(f"  bet_type: {bet.bet_type}")
            print(f"  created_at: {bet.created_at}")
            
            game_ids_before = sum(1 for leg in bet.bet_legs_rel if leg.game_id)
            print(f"  Legs with game_id: {game_ids_before}/{len(bet.bet_legs_rel)}")
            
            # Fix 1: Set betting_site and bet_type from bet_data JSON
            print(f"\n🔧 STEP 1: Fix betting_site and bet_type from JSON...")
            try:
                if bet.bet_data:
                    bet_data = json.loads(bet.bet_data)
                    
                    # Extract values from JSON
                    betting_site = bet_data.get('betting_site')
                    bet_type_val = bet_data.get('bet_type')
                    
                    print(f"  From JSON: betting_site={betting_site}, bet_type={bet_type_val}")
                    
                    # Set to database if values exist
                    if betting_site:
                        bet.betting_site = betting_site
                    if bet_type_val:
                        bet.bet_type = bet_type_val
                    else:
                        bet.bet_type = 'Parlay'  # Default
                    
                    # Ensure created_at is set
                    if not bet.created_at:
                        bet.created_at = datetime.now()
                    
                    db.session.commit()
                    print(f"  ✅ Updated: betting_site={bet.betting_site}, bet_type={bet.bet_type}")
                else:
                    print(f"  ⚠️  No bet_data stored, skipping")
            except Exception as e:
                print(f"  ❌ Error: {e}")
                db.session.rollback()
                continue
            
            # Fix 2: Manually populate game IDs by matching home_team to ESPN games
            print(f"\n🔧 STEP 2: Manually populate game_ids by matching on home_team...")
            try:
                # Get the game date from the first leg
                game_date = bet.bet_legs_rel[0].game_date if bet.bet_legs_rel else None
                
                if not game_date:
                    print(f"  ⚠️  No game_date found, skipping")
                else:
                    print(f"  Fetching ESPN games for {game_date}...")
                    games = get_espn_games_with_ids_for_date(game_date)
                    
                    if not games:
                        print(f"  ⚠️  No games found for {game_date}")
                    else:
                        # Create lookup: home_team_name -> game_id
                        game_lookup = {}
                        for game_id, away_team, home_team in games:
                            home_norm = home_team.lower().strip()
                            game_lookup[home_norm] = (game_id, away_team)
                            print(f"    Found game: {away_team} @ {home_team} (ID: {game_id})")
                        
                        # Match each leg's home_team to ESPN games
                        matched = 0
                        for leg in bet.bet_legs_rel:
                            home_norm = leg.home_team.lower().strip() if leg.home_team else None
                            
                            if home_norm and home_norm in game_lookup:
                                game_id, opponent = game_lookup[home_norm]
                                leg.game_id = game_id
                                # Also update away_team if it was TBD
                                if leg.away_team == 'TBD':
                                    leg.away_team = opponent
                                matched += 1
                                print(f"    ✅ Leg {leg.id}: Matched {leg.home_team} (home) to game {game_id}")
                            else:
                                print(f"    ❌ Leg {leg.id}: No match for {leg.home_team}")
                        
                        db.session.commit()
                        print(f"  ✅ Matched {matched}/{len(bet.bet_legs_rel)} legs to ESPN games")
                        
            except Exception as e:
                print(f"  ❌ Error: {e}")
                db.session.rollback()
                import traceback
                traceback.print_exc()
            
            # Refresh bet object
            db.session.expire(bet)
            
            # Show after state
            print(f"\n📊 AFTER FIX:")
            print(f"  betting_site: {bet.betting_site}")
            print(f"  bet_type: {bet.bet_type}")
            print(f"  created_at: {bet.created_at}")
            
            game_ids_after = sum(1 for leg in bet.bet_legs_rel if leg.game_id)
            print(f"  Legs with game_id: {game_ids_after}/{len(bet.bet_legs_rel)}")
            
            # Show detailed leg status
            print(f"\n📈 LEG DETAILS:")
            for i, leg in enumerate(bet.bet_legs_rel, 1):
                status = "✅" if leg.game_id else "❌"
                player_info = leg.player_name or f"{leg.away_team} @ {leg.home_team}"
                print(f"  Leg {i}: {player_info}")
                print(f"    game_id={leg.game_id if leg.game_id else 'MISSING'} {status}")
                print(f"    teams: {leg.away_team} @ {leg.home_team}")
        
        print(f"\n{'='*80}")
        print(f"✅ FIX COMPLETE")
        print(f"{'='*80}")

if __name__ == '__main__':
    fix_bets_158_160()
