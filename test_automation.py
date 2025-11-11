#!/usr/bin/env python3
"""Test script to verify the automated bet leg update function works correctly."""

import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, update_completed_bet_legs, Bet, BetLeg

def test_automation():
    """Test the automated bet leg update function."""
    with app.app_context():
        print("=" * 60)
        print("Testing Automated Bet Leg Updates")
        print("=" * 60)
        
        # Check current state
        completed_bets = Bet.query.filter_by(status='completed').all()
        print(f"\n✓ Found {len(completed_bets)} completed bets")
        
        if completed_bets:
            # Show sample bet info
            sample_bet = completed_bets[0]
            print(f"\nSample bet ID: {sample_bet.id}")
            print(f"User: {sample_bet.user_id}")
            print(f"Created: {sample_bet.created_at}")
            
            # Show legs
            legs = sample_bet.bet_legs_rel.all()
            print(f"Number of legs: {len(legs)}")
            
            for i, leg in enumerate(legs, 1):
                print(f"\nLeg {i}:")
                print(f"  Player/Team: {leg.player_name or leg.team or 'N/A'}")
                print(f"  Bet Type: {leg.bet_type}")
                print(f"  Game Status: {leg.game_status}")
                print(f"  Achieved Value: {leg.achieved_value}")
                print(f"  Status: {leg.status}")
        
        # Run the automation
        print("\n" + "=" * 60)
        print("Running update_completed_bet_legs()...")
        print("=" * 60 + "\n")
        
        try:
            update_completed_bet_legs()
            print("\n✓ Automation completed successfully")
        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Check results after update
        print("\n" + "=" * 60)
        print("Checking Results After Update")
        print("=" * 60)
        
        if completed_bets:
            sample_bet = Bet.query.get(sample_bet.id)
            legs = sample_bet.bet_legs_rel.all()
            
            for i, leg in enumerate(legs, 1):
                print(f"\nLeg {i}:")
                print(f"  Player/Team: {leg.player_name or leg.team or 'N/A'}")
                print(f"  Game Status: {leg.game_status}")
                print(f"  Achieved Value: {leg.achieved_value}")
                print(f"  Status: {leg.status}")
        
        print("\n" + "=" * 60)
        print("Test Complete!")
        print("=" * 60)
        
        return True

if __name__ == "__main__":
    success = test_automation()
    sys.exit(0 if success else 1)
