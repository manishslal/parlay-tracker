#!/usr/bin/env python3
"""
Backfill Historical Bet Stats
==============================
One-time script to fetch and save final stats for historical bets that are missing them.

This ensures all completed bets have hardcoded stats and won't need ESPN API calls
on every refresh of the Historical Bets page.

Usage:
    python backfill_historical_stats.py
"""

import os
import sys
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, has_complete_final_data, save_final_results_to_bet, process_parlay_data
from models import User, Bet

def backfill_missing_stats():
    """Find all historical bets missing final stats and fetch them from ESPN"""
    
    with app.app_context():
        print("\n" + "="*60)
        print("BACKFILL HISTORICAL BET STATS")
        print("="*60)
        
        # Get all historical bets (is_active=False)
        historical_bets = Bet.query.filter_by(is_active=False).all()
        
        print(f"\nFound {len(historical_bets)} historical bets")
        
        if not historical_bets:
            print("✅ No historical bets found - nothing to backfill")
            return
        
        # Separate bets with/without complete data
        bets_with_data = []
        bets_missing_data = []
        
        for bet in historical_bets:
            bet_data = bet.get_bet_data()
            if has_complete_final_data(bet_data):
                bets_with_data.append(bet)
            else:
                bets_missing_data.append(bet)
        
        print(f"  ✅ {len(bets_with_data)} bets already have complete final data")
        print(f"  ⚠️  {len(bets_missing_data)} bets missing final stats")
        
        if not bets_missing_data:
            print("\n✅ All historical bets already have complete data!")
            return
        
        print(f"\n{'='*60}")
        print("FETCHING MISSING STATS FROM ESPN")
        print("="*60)
        
        success_count = 0
        failed_count = 0
        
        for bet in bets_missing_data:
            bet_data = bet.get_bet_data()
            bet_name = bet_data.get('name', f'Bet #{bet.id}')
            
            print(f"\nProcessing: {bet_name}")
            print(f"  Bet ID: {bet.id}")
            print(f"  Legs: {len(bet_data.get('legs', []))}")
            
            try:
                # Fetch current data from ESPN
                processed_data = process_parlay_data([bet_data])
                
                if processed_data:
                    # Save final results
                    saved = save_final_results_to_bet(bet, processed_data)
                    
                    if saved:
                        bet.api_fetched = 'Yes'
                        db.session.commit()
                        print(f"  ✅ Successfully saved final stats")
                        success_count += 1
                    else:
                        print(f"  ⚠️  No data saved (games may not be final yet)")
                        failed_count += 1
                else:
                    print(f"  ❌ Failed to fetch ESPN data")
                    failed_count += 1
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
                failed_count += 1
                db.session.rollback()
        
        print(f"\n{'='*60}")
        print("BACKFILL COMPLETE")
        print("="*60)
        print(f"✅ Successfully backfilled: {success_count} bets")
        print(f"❌ Failed/Incomplete: {failed_count} bets")
        
        if failed_count > 0:
            print(f"\nNote: Some bets may have failed because:")
            print("  - Games are too old and ESPN no longer has the data")
            print("  - Games haven't finished yet (not STATUS_FINAL)")
            print("  - Network/API errors")
            print("\nThese bets will still display but may show incomplete data.")

if __name__ == "__main__":
    backfill_missing_stats()
