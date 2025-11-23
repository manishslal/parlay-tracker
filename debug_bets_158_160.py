#!/usr/bin/env python3
"""
Debug script to analyze why bets 158, 159, 160 weren't linked to ESPN game IDs
and why their information wasn't processed correctly.
"""

import sys
import os
sys.path.append('/Users/manishslal/Desktop/Scrapper')

from dotenv import load_dotenv
load_dotenv()

from app import app, db
from models import Bet, BetLeg, Player

def analyze_problematic_bets():
    """Analyze bets 158, 159, 160 in detail."""
    
    with app.app_context():
        bet_ids = [158, 159, 160]
        
        for bet_id in bet_ids:
            bet = Bet.query.get(bet_id)
            
            if not bet:
                print(f"❌ Bet {bet_id} not found!")
                continue
            
            print(f"\n{'='*80}")
            print(f"🔍 ANALYZING BET {bet_id}")
            print(f"{'='*80}")
            
            # Basic info
            print(f"\n📋 BET INFORMATION")
            print(f"  User ID: {bet.user_id}")
            print(f"  Betting Site: {bet.betting_site}")
            print(f"  Bet Type: {bet.bet_type}")
            print(f"  Status: {bet.status}")
            print(f"  Created: {bet.created_at}")
            print(f"  Wager: ${bet.wager}")
            print(f"  Final Odds: {bet.final_odds}")
            print(f"  Potential Winnings: ${bet.potential_winnings}")
            
            print(f"\n📊 LEG ANALYSIS ({len(bet.bet_legs_rel)} legs)")
            print(f"{'─'*80}")
            
            for i, leg in enumerate(bet.bet_legs_rel, 1):
                print(f"\n  Leg {i}:")
                print(f"    ID: {leg.id}")
                print(f"    Player: {leg.player_name}")
                print(f"    Team: {leg.player_team}")
                print(f"    Home: {leg.home_team} vs Away: {leg.away_team}")
                print(f"    Stat: {leg.stat_type}")
                print(f"    Target: {leg.target_value}")
                print(f"    Sport: {leg.sport}")
                print(f"    Game ID: {leg.game_id if leg.game_id else '❌ MISSING'}")
                print(f"    Player ID: {leg.player_id if leg.player_id else '❌ MISSING'}")
                print(f"    Status: {leg.status}")
                
                # Check if game_id is missing
                if not leg.game_id:
                    print(f"    ⚠️  GAME_ID MISSING - Possible issues:")
                    print(f"       - ESPN API lookup might have failed")
                    print(f"       - Team names might not match ESPN format")
                    print(f"       - Game might not exist in ESPN database")
                    print(f"       - populate_game_ids_for_bet() might not have run")
                
                # Check if player_id is missing
                if not leg.player_id and leg.player_name:
                    print(f"    ⚠️  PLAYER_ID MISSING - Possible issues:")
                    print(f"       - Player lookup might have failed")
                    print(f"       - populate_player_data_for_bet() might not have run")
            
            # Check raw bet_data JSON
            print(f"\n📄 BET_DATA (raw JSON)")
            print(f"{'─'*80}")
            if bet.bet_data:
                import json
                try:
                    bet_data = json.loads(bet.bet_data)
                    print(f"Keys: {list(bet_data.keys())}")
                    print(f"Legs in JSON: {len(bet_data.get('legs', []))}")
                except Exception as e:
                    print(f"Error parsing: {e}")
            else:
                print("No bet_data stored")
            
            # Summary of issues
            print(f"\n⚠️  ISSUES SUMMARY FOR BET {bet_id}")
            print(f"{'─'*80}")
            missing_game_ids = sum(1 for leg in bet.bet_legs_rel if not leg.game_id)
            missing_player_ids = sum(1 for leg in bet.bet_legs_rel if not leg.player_id and leg.player_name)
            
            if missing_game_ids > 0:
                print(f"  ❌ {missing_game_ids}/{len(bet.bet_legs_rel)} legs missing game_id")
            else:
                print(f"  ✅ All legs have game_id")
            
            if missing_player_ids > 0:
                print(f"  ❌ {missing_player_ids}/{len(bet.bet_legs_rel)} legs missing player_id")
            else:
                print(f"  ✅ All legs have player_id")
            
            # Check if betting_site/bet_type were set
            if not bet.betting_site:
                print(f"  ❌ betting_site is None")
            else:
                print(f"  ✅ betting_site set to: {bet.betting_site}")
            
            if not bet.bet_type:
                print(f"  ❌ bet_type is None")
            else:
                print(f"  ✅ bet_type set to: {bet.bet_type}")

if __name__ == '__main__':
    analyze_problematic_bets()
