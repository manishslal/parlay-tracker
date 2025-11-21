#!/usr/bin/env python3
"""
Fix Woody Marks stat type from passing_yards to rushing_yards
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Bet, BetLeg

def fix_woody_marks_stat():
    """Fix Woody Marks stat type from passing_yards to rushing_yards"""
    with app.app_context():
        # Find bet legs for Woody Marks with passing_yards
        woody_legs = BetLeg.query.filter(
            BetLeg.player_name.ilike('%woody%marks%'),
            BetLeg.stat_type == 'passing_yards'
        ).all()

        if not woody_legs:
            print("❌ No Woody Marks legs with passing_yards found")
            return False

        print(f"Found {len(woody_legs)} Woody Marks legs with passing_yards:")

        fixed_count = 0
        for leg in woody_legs:
            print(f"  Bet {leg.bet_id}, Leg {leg.id}: {leg.player_name} - {leg.stat_type}")

            # Update to rushing_yards
            leg.stat_type = 'rushing_yards'
            fixed_count += 1

            print(f"    ✅ Updated to: {leg.stat_type}")

        if fixed_count > 0:
            db.session.commit()
            print(f"\n✅ Successfully updated {fixed_count} legs")
            return True
        else:
            print("\n❌ No legs were updated")
            return False

if __name__ == "__main__":
    print("🔧 Fixing Woody Marks stat type")
    print("=" * 40)

    if fix_woody_marks_stat():
        print("\n🎉 Woody Marks stat type has been corrected to rushing_yards!")
        print("   The bet should now show the correct stat on the frontend.")
    else:
        print("\n❌ Failed to fix Woody Marks stat type")