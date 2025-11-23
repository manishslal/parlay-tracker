#!/usr/bin/env python3
"""
Manual fix script for bets 158-160.
This script will:
1. Fix the betting_site and bet_type fields
2. Populate missing game_ids by matching to ESPN
3. Verify all data is correct
4. Display before/after comparison
"""

import sys
import os
sys.path.append('/Users/manishslal/Desktop/Scrapper')

from dotenv import load_dotenv
load_dotenv()

from app import app, db, populate_game_ids_for_bet, populate_player_data_for_bet
from models import Bet, BetLeg
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
            player_ids_before = sum(1 for leg in bet.bet_legs_rel if leg.player_id)
            print(f"  Legs with game_id: {game_ids_before}/{len(bet.bet_legs_rel)}")
            print(f"  Legs with player_id: {player_ids_before}/{len(bet.bet_legs_rel)}")
            
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
            
            # Fix 2: Populate game IDs
            print(f"\n🔧 STEP 2: Populate missing game_ids...")
            try:
                populate_game_ids_for_bet(bet)
                game_ids_after = sum(1 for leg in bet.bet_legs_rel if leg.game_id)
                print(f"  ✅ Game IDs populated: {game_ids_before} → {game_ids_after}/{len(bet.bet_legs_rel)}")
            except Exception as e:
                print(f"  ❌ Error: {e}")
            
            # Fix 3: Populate player data
            print(f"\n🔧 STEP 3: Populate missing player_ids...")
            try:
                populate_player_data_for_bet(bet)
                player_ids_after = sum(1 for leg in bet.bet_legs_rel if leg.player_id)
                print(f"  ✅ Player IDs populated: {player_ids_before} → {player_ids_after}/{len(bet.bet_legs_rel)}")
            except Exception as e:
                print(f"  ❌ Error: {e}")
            
            # Refresh from database
            db.session.refresh(bet)
            
            # Show after state
            print(f"\n📊 AFTER FIX:")
            print(f"  betting_site: {bet.betting_site}")
            print(f"  bet_type: {bet.bet_type}")
            print(f"  created_at: {bet.created_at}")
            
            game_ids_after = sum(1 for leg in bet.bet_legs_rel if leg.game_id)
            player_ids_after = sum(1 for leg in bet.bet_legs_rel if leg.player_id)
            print(f"  Legs with game_id: {game_ids_after}/{len(bet.bet_legs_rel)}")
            print(f"  Legs with player_id: {player_ids_after}/{len(bet.bet_legs_rel)}")
            
            # Show detailed leg status
            print(f"\n📈 LEG DETAILS:")
            for i, leg in enumerate(bet.bet_legs_rel, 1):
                status = "✅" if leg.game_id else "❌"
                print(f"  Leg {i}: {leg.player_name or leg.home_team} - "
                      f"game_id={leg.game_id if leg.game_id else 'MISSING'} "
                      f"player_id={leg.player_id if leg.player_id else 'N/A'} {status}")
        
        print(f"\n{'='*80}")
        print(f"✅ FIX COMPLETE")
        print(f"{'='*80}")

if __name__ == '__main__':
    fix_bets_158_160()
