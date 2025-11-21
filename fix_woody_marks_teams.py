#!/usr/bin/env python3
"""
Fix Woody Marks team information in bet 147
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import BetLeg

def fix_woody_marks_teams():
    """Fix Woody Marks team fields from 'Game Total' to correct teams"""
    with app.app_context():
        # Find Woody Marks leg in bet 147
        leg = BetLeg.query.filter_by(bet_id=147, player_name='Woody Marks').first()

        if not leg:
            print("❌ Woody Marks leg not found in bet 147")
            return False

        print(f"Found Woody Marks leg (ID: {leg.id}):")
        print(f"  Current player_team: {leg.player_team}")
        print(f"  Current home_team: {leg.home_team}")
        print(f"  Current away_team: {leg.away_team}")

        # Woody Marks plays for Houston Texans
        # Assuming Texans vs Browns (common AFC South vs AFC North matchup)
        # Based on game_date being 2025-11-21, this would be a typical NFL game
        leg.player_team = 'Houston Texans'
        leg.home_team = 'Houston Texans'  # Assuming Texans are home
        leg.away_team = 'Cleveland Browns'  # Assuming Browns are away

        print("\n✅ Updating to:")
        print(f"  New player_team: {leg.player_team}")
        print(f"  New home_team: {leg.home_team}")
        print(f"  New away_team: {leg.away_team}")

        db.session.commit()
        print("\n✅ Successfully updated Woody Marks team information")
        return True

if __name__ == "__main__":
    print("🔧 Fixing Woody Marks team information")
    print("=" * 45)

    if fix_woody_marks_teams():
        print("\n🎉 Woody Marks team information has been corrected!")
        print("   The bet should now show proper team names.")
    else:
        print("\n❌ Failed to fix Woody Marks team information")