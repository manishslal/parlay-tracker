#!/usr/bin/env python3
"""
Fix bet 146 game dates for historical processing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import BetLeg
from datetime import date

def fix_bet_146_dates():
    """Update bet 146 legs to have correct game date"""
    with app.app_context():
        print("Fixing bet 146 game dates...")

        # Update bet 146 legs to have the correct game date
        legs = BetLeg.query.filter_by(bet_id=146).all()
        correct_date = date(2025, 11, 16)

        updated_count = 0
        for leg in legs:
            if leg.game_date != correct_date:
                print(f'Updating leg {leg.id}: {leg.game_date} -> {correct_date}')
                leg.game_date = correct_date
                updated_count += 1

        if updated_count > 0:
            db.session.commit()
            print(f"Updated {updated_count} legs with correct date")
        else:
            print("No updates needed - dates already correct")

if __name__ == "__main__":
    fix_bet_146_dates()