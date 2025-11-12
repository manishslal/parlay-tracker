#!/usr/bin/env python
"""Test script for team name normalization on startup"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app, normalize_bet_leg_team_names
from models import db, BetLeg, Team

def test_normalization():
    """Test the team name normalization function"""
    print("=" * 60)
    print("Testing Team Name Normalization")
    print("=" * 60)
    
    with app.app_context():
        # Show sample data before normalization
        print("\n📊 Sample bet_legs BEFORE normalization:")
        print("-" * 60)
        
        sample_legs = BetLeg.query.limit(10).all()
        for leg in sample_legs:
            print(f"\nLeg ID: {leg.id}")
            print(f"  home_team: '{leg.home_team}'")
            print(f"  away_team: '{leg.away_team}'")
            print(f"  player_team: '{leg.player_team}'")
            print(f"  status: {leg.status}")
            print(f"  is_hit: {leg.is_hit}")
        
        # Show teams table data
        print("\n\n📋 Teams table reference:")
        print("-" * 60)
        teams = Team.query.limit(10).all()
        for team in teams:
            print(f"{team.team_abbr:5} | {team.nickname:15} | {team.team_name}")
        
        # Run normalization
        print("\n\n🔄 Running normalization...")
        print("=" * 60)
        normalize_bet_leg_team_names()
        
        # Show sample data after normalization
        print("\n\n✅ Sample bet_legs AFTER normalization:")
        print("-" * 60)
        
        sample_legs = BetLeg.query.limit(10).all()
        for leg in sample_legs:
            print(f"\nLeg ID: {leg.id}")
            print(f"  home_team: '{leg.home_team}'")
            print(f"  away_team: '{leg.away_team}'")
            print(f"  player_team: '{leg.player_team}'")
            print(f"  status: {leg.status}")
            print(f"  is_hit: {leg.is_hit}")
        
        # Statistics
        print("\n\n📈 Statistics:")
        print("=" * 60)
        total_legs = BetLeg.query.count()
        completed_bets = BetLeg.query.join(BetLeg.bet).filter_by(is_active=False, status='completed').count()
        pending_status = BetLeg.query.filter_by(status='pending').count()
        null_is_hit = BetLeg.query.filter(BetLeg.is_hit.is_(None)).count()
        
        print(f"Total bet legs: {total_legs}")
        print(f"Legs in completed bets: {completed_bets}")
        print(f"Legs with pending status: {pending_status}")
        print(f"Legs with null is_hit: {null_is_hit}")
        
        print("\n" + "=" * 60)
        print("✓ Test complete!")
        print("=" * 60)

if __name__ == "__main__":
    test_normalization()
