#!/usr/bin/env python3
"""
Standardize team names in bet_legs table to use team_name_short from teams table.
Updates player_team, home_team, and away_team columns to ensure consistency.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import BetLeg, Team

def standardize_team_names():
    with app.app_context():
        print("\n=== Team Name Standardization: Update bet_legs to use team_name_short ===\n")

        # Get all teams for mapping
        teams = Team.query.all()
        print(f"Found {len(teams)} teams in database")

        # Create sport-specific mapping dictionaries
        nfl_name_to_short = {}
        nfl_abbr_to_short = {}
        nba_name_to_short = {}
        nba_abbr_to_short = {}

        for team in teams:
            if team.sport == 'NFL':
                if team.team_name:
                    nfl_name_to_short[team.team_name.lower()] = team.team_name_short
                if team.team_name_short:
                    nfl_name_to_short[team.team_name_short.lower()] = team.team_name_short
                if team.team_abbr:
                    nfl_abbr_to_short[team.team_abbr.lower()] = team.team_name_short
            elif team.sport == 'NBA':
                if team.team_name:
                    nba_name_to_short[team.team_name.lower()] = team.team_name_short
                if team.team_name_short:
                    nba_name_to_short[team.team_name_short.lower()] = team.team_name_short
                if team.team_abbr:
                    nba_abbr_to_short[team.team_abbr.lower()] = team.team_name_short

        print(f"Created mappings: NFL={len(nfl_name_to_short)} names/{len(nfl_abbr_to_short)} abbrs, NBA={len(nba_name_to_short)} names/{len(nba_abbr_to_short)} abbrs")

        # Get all bet legs
        bet_legs = BetLeg.query.all()
        print(f"\nFound {len(bet_legs)} bet legs to process\n")

        updated_count = 0
        error_count = 0

        for leg in bet_legs:
            original_player_team = leg.player_team
            original_home_team = leg.home_team
            original_away_team = leg.away_team

            # Choose the appropriate mapping based on the bet leg's sport
            if leg.sport == 'NFL':
                name_to_short = nfl_name_to_short
                abbr_to_short = nfl_abbr_to_short
            elif leg.sport == 'NBA':
                name_to_short = nba_name_to_short
                abbr_to_short = nba_abbr_to_short
            else:
                # For unknown sports, try NFL first, then NBA
                name_to_short = {**nfl_name_to_short, **nba_name_to_short}
                abbr_to_short = {**nfl_abbr_to_short, **nba_abbr_to_short}

            # Update player_team if it exists
            if leg.player_team:
                new_player_team = find_team_name_short(leg.player_team, name_to_short, abbr_to_short)
                if new_player_team and new_player_team != leg.player_team:
                    leg.player_team = new_player_team

            # Update home_team
            if leg.home_team:
                new_home_team = find_team_name_short(leg.home_team, name_to_short, abbr_to_short)
                if new_home_team and new_home_team != leg.home_team:
                    leg.home_team = new_home_team

            # Update away_team
            if leg.away_team:
                new_away_team = find_team_name_short(leg.away_team, name_to_short, abbr_to_short)
                if new_away_team and new_away_team != leg.away_team:
                    leg.away_team = new_away_team

            # Check if any updates were made
            if (leg.player_team != original_player_team or
                leg.home_team != original_home_team or
                leg.away_team != original_away_team):

                try:
                    db.session.commit()
                    updated_count += 1
                    print(f"✓ Updated bet_leg {leg.id} ({leg.sport}):")
                    if leg.player_team != original_player_team:
                        print(f"  player_team: '{original_player_team}' -> '{leg.player_team}'")
                    if leg.home_team != original_home_team:
                        print(f"  home_team: '{original_home_team}' -> '{leg.home_team}'")
                    if leg.away_team != original_away_team:
                        print(f"  away_team: '{original_away_team}' -> '{leg.away_team}'")
                except Exception as e:
                    db.session.rollback()
                    error_count += 1
                    print(f"✗ Error updating bet_leg {leg.id}: {e}")

        print(f"\n=== Migration Complete ===")
        print(f"✓ Successfully updated: {updated_count} bet legs")
        if error_count > 0:
            print(f"✗ Errors: {error_count} bet legs")
        print(f"Total processed: {len(bet_legs)} bet legs")

def find_team_name_short(team_name, name_to_short, abbr_to_short):
    """Find the team_name_short for a given team name using various matching strategies."""
    if not team_name or not team_name.strip():
        return None

    team_name_lower = team_name.lower().strip()

    # Direct match in name_to_short
    if team_name_lower in name_to_short:
        return name_to_short[team_name_lower]

    # Check if it's an abbreviation
    if team_name_lower in abbr_to_short:
        return abbr_to_short[team_name_lower]

    # Try partial matching for common abbreviations
    # Check if it's a common abbreviation pattern
    if len(team_name) <= 3 and team_name.isupper():
        if team_name_lower in abbr_to_short:
            return abbr_to_short[team_name_lower]

    # Try to match by extracting last word (for names like "Kansas City Chiefs" -> "Chiefs")
    if ' ' in team_name:
        last_word = team_name.split()[-1].lower()
        if last_word in name_to_short:
            return name_to_short[last_word]

    # Try to match by extracting first word (for names like "New England Patriots" -> "Patriots" might be in abbr)
    if ' ' in team_name:
        first_word = team_name.split()[0].lower()
        if first_word in abbr_to_short:
            return abbr_to_short[first_word]

    # If no match found, return None (don't change)
    return None

if __name__ == "__main__":
    print("Starting team name standardization migration...")
    standardize_team_names()
    print("Migration completed!")