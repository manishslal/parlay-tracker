"""
Team Name Standardization Automation

Standardizes team names in bet_legs to use team_name_short from teams table.
Runs daily to ensure consistent team naming across the database.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from helpers.team_utils import find_team_name_short


def standardize_bet_leg_team_names():
    """Background job to standardize team names in bet_legs to use team_name_short from teams table.
    
    This runs periodically to ensure all bet_legs have consistent team names that match
    the standardized team_name_short values from the teams table.
    """
    from app import app, db
    from models import Team, BetLeg
    
    try:
        import logging
        logging.info("[TEAM-STANDARDIZE] Starting team name standardization check...")
        
        # Get all teams for mapping
        teams = Team.query.all()
        
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
        
        # Get all bet legs
        bet_legs = BetLeg.query.all()
        updated_count = 0
        
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
                except Exception as e:
                    db.session.rollback()
                    logging.error(f"[TEAM-STANDARDIZE] Error updating bet_leg {leg.id}: {e}")
        
        if updated_count > 0:
            logging.info(f"[TEAM-STANDARDIZE] ✓ Standardized team names for {updated_count} bet legs")
        else:
            logging.info("[TEAM-STANDARDIZE] No bet legs needed team name standardization")
            
    except Exception as e:
        logging.error(f"[TEAM-STANDARDIZE] Error in standardize_bet_leg_team_names: {e}")
        db.session.rollback()