#!/usr/bin/env python3
"""
Populate ESPN game IDs for all bet legs that have game dates but missing game IDs.
This ensures all bet legs have correct ESPN game IDs for live game tracking.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Bet, BetLeg
from helpers.espn_api import get_espn_games_with_ids_for_date

def find_game_id_for_existing_match(away_team: str, home_team: str, game_date: datetime) -> Optional[str]:
    """
    Find the ESPN game ID for an existing game matchup on a specific date.
    """
    if not away_team or not home_team or not game_date:
        return None

    try:
        games = get_espn_games_with_ids_for_date(game_date)
        if games:
            for game_id, espn_away, espn_home in games:
                # Check for exact match (allowing for team name variations)
                if ((away_team.lower() in espn_away.lower() or espn_away.lower() in away_team.lower()) and
                    (home_team.lower() in espn_home.lower() or espn_home.lower() in home_team.lower())):
                    return game_id
                # Also check reverse order
                if ((away_team.lower() in espn_home.lower() or espn_home.lower() in away_team.lower()) and
                    (home_team.lower() in espn_away.lower() or espn_away.lower() in home_team.lower())):
                    return game_id
    except Exception as e:
        print(f"   Error fetching games for {game_date.strftime('%Y-%m-%d')}: {e}")

    return None

def populate_game_ids():
    """Populate ESPN game IDs for all bet legs that have game dates but missing game IDs."""

    with app.app_context():
        print("=" * 100)
        print("POPULATE ESPN GAME IDs FOR ALL BET LEGS")
        print("=" * 100)

        # Get all bet legs that have game dates but no game_id
        legs_needing_ids = BetLeg.query.filter(
            BetLeg.game_date.isnot(None),
            BetLeg.away_team.isnot(None),
            BetLeg.home_team.isnot(None),
            (BetLeg.game_id.is_(None) | (BetLeg.game_id == ''))
        ).all()

        print(f"Found {len(legs_needing_ids)} bet legs with game dates but missing game IDs")

        updated_count = 0
        error_count = 0

        for leg in legs_needing_ids:
            print(f"\n🔍 Processing Leg {leg.id}: {leg.away_team} @ {leg.home_team} on {leg.game_date}")

            # Find the ESPN game ID for this matchup
            game_id = find_game_id_for_existing_match(leg.away_team, leg.home_team, leg.game_date)

            if game_id:
                try:
                    leg.game_id = game_id
                    db.session.commit()
                    updated_count += 1
                    print(f"   ✅ Updated with ESPN game ID: {game_id}")
                except Exception as e:
                    db.session.rollback()
                    error_count += 1
                    print(f"   ❌ Error updating database: {e}")
            else:
                print(f"   ⚠️ No ESPN game ID found for this matchup")
                error_count += 1

        print(f"\n{'='*100}")
        print("SUMMARY:")
        print(f"   ✅ Successfully updated: {updated_count} bet legs")
        print(f"   ❌ Errors/Not found: {error_count} bet legs")
        print(f"   📊 Total processed: {len(legs_needing_ids)} bet legs")
        print(f"{'='*100}")

if __name__ == "__main__":
    populate_game_ids()