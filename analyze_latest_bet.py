#!/usr/bin/env python3
"""
Analyze the latest uploaded bet to identify any issues.
"""

import sys
import os
sys.path.append('/Users/manishslal/Desktop/Scrapper')

from dotenv import load_dotenv
load_dotenv()

from app import app, db
from models import Bet, BetLeg, Player
from datetime import datetime, timedelta

def analyze_latest_bet():
    """Analyze the most recent bet to identify issues."""
    
    with app.app_context():
        # Get the most recent bet
        latest_bet = Bet.query.order_by(Bet.created_at.desc()).first()
        
        if not latest_bet:
            print("❌ No bets found in database!")
            return False
        
        print(f"\n{'='*70}")
        print(f"📊 ANALYZING LATEST BET")
        print(f"{'='*70}")
        print(f"Bet ID: {latest_bet.id}")
        print(f"Created: {latest_bet.created_at}")
        print(f"User: {latest_bet.user_id}")
        print(f"Betting Site: {latest_bet.betting_site}")
        print(f"Bet Type: {latest_bet.bet_type}")
        print(f"Bet Date: {latest_bet.bet_date}")
        print(f"Wager: ${latest_bet.wager}")
        print(f"Final Odds: {latest_bet.final_odds}")
        print(f"Potential Winnings: ${latest_bet.potential_winnings}")
        print(f"Legs Count: {len(latest_bet.bet_legs_rel)}")
        
        print(f"\n{'='*70}")
        print(f"🔍 LEG ANALYSIS")
        print(f"{'='*70}")
        
        all_issues = []
        
        for i, leg in enumerate(latest_bet.bet_legs_rel, 1):
            print(f"\n--- Leg {i} ---")
            print(f"  ID: {leg.id}")
            print(f"  Home Team: {leg.home_team}")
            print(f"  Away Team: {leg.away_team}")
            print(f"  Player: {leg.player_name}")
            print(f"  Stat: {leg.stat_type}")
            print(f"  Target: {leg.target_value}")
            print(f"  Bet Type: {leg.bet_type}")
            print(f"  Game ID: {leg.game_id if leg.game_id else '❌ MISSING'}")
            print(f"  Player ID: {leg.player_id if leg.player_id else '❌ MISSING'}")
            print(f"  Status: {leg.status}")
            print(f"  Is Hit: {leg.is_hit}")
            
            # Collect issues
            if not leg.game_id:
                all_issues.append(f"Leg {i}: Missing game_id (ESPN linking failed?)")
            if not leg.player_id and leg.player_name:
                all_issues.append(f"Leg {i}: Missing player_id for {leg.player_name}")
            if leg.home_team == 'TBD' or leg.away_team == 'TBD':
                all_issues.append(f"Leg {i}: TBD team name detected - game matching incomplete")
        
        # Check secondary bettors
        print(f"\n{'='*70}")
        print(f"👥 SECONDARY BETTORS")
        print(f"{'='*70}")
        if latest_bet.secondary_bettors:
            print(f"Count: {len(latest_bet.secondary_bettors)}")
            for bettor in latest_bet.secondary_bettors:
                print(f"  - {bettor.username} (ID: {bettor.id})")
        else:
            print("None")
        
        # Summary
        print(f"\n{'='*70}")
        print(f"⚠️  ISSUES FOUND")
        print(f"{'='*70}")
        
        if all_issues:
            for issue in all_issues:
                print(f"  ❌ {issue}")
        else:
            print("  ✅ No obvious issues detected!")
        
        # Quick game check
        print(f"\n{'='*70}")
        print(f"📅 GAME LOOKUP STATUS")
        print(f"{'='*70}")
        
        games_with_ids = sum(1 for leg in latest_bet.bet_legs_rel if leg.game_id)
        print(f"Legs with game_id: {games_with_ids}/{len(latest_bet.bet_legs_rel)}")
        
        # Quick player check
        players_with_ids = sum(1 for leg in latest_bet.bet_legs_rel if leg.player_id)
        legs_with_players = sum(1 for leg in latest_bet.bet_legs_rel if leg.player_name)
        if legs_with_players > 0:
            print(f"Legs with player_id: {players_with_ids}/{legs_with_players}")
        
        # Return success if no critical issues
        critical_issues = [i for i in all_issues if 'Missing game_id' in i or 'Missing player_id' in i]
        
        return len(critical_issues) == 0

if __name__ == '__main__':
    success = analyze_latest_bet()
    sys.exit(0 if success else 1)
