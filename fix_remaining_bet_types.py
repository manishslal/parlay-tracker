
import sys
import os
import logging
from sqlalchemy import or_, func

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add current directory to path
sys.path.append(os.getcwd())

from app import app, db
from models import BetLeg

def fix_remaining_bet_types():
    """
    Aggressively fix ALL bet legs to ensure bet_type is EITHER 'Team Prop' OR 'Player Prop'.
    """
    with app.app_context():
        try:
            logger.info("Starting comprehensive bet type fix...")
            
            # Get all bet legs
            legs = BetLeg.query.all()
            logger.info(f"Found {len(legs)} legs to process")
            
            updated_count = 0
            
            # Define Team Prop keywords (lowercase)
            team_prop_keywords = [
                'moneyline', 'spread', 'total', 'over', 'under', 'game', 'team', 
                'points', 'score'
            ]
            
            # Define specific Team Prop types
            team_prop_types = [
                'moneyline', 'spread', 'total_points', 'over_under', 
                'team_total', 'total', 'game_line', 'game_total', 'team_prop'
            ]
            
            for leg in legs:
                original_bet_type = leg.bet_type
                original_stat_type = leg.stat_type
                
                # Normalize current values
                curr_bet_type_lower = str(original_bet_type).lower().strip() if original_bet_type else ''
                curr_stat_type_lower = str(original_stat_type).lower().strip() if original_stat_type else ''
                
                new_bet_type = None
                new_stat_type = original_stat_type
                
                # 1. Check if it's already correct (case-sensitive check)
                if original_bet_type == 'Team Prop' or original_bet_type == 'Player Prop':
                    # Even if correct, ensure stat_type isn't empty if bet_type was generic
                    if not new_stat_type:
                         # If stat_type is empty, leave it empty or try to infer? 
                         # For now, let's just trust it unless we have a reason to change.
                         continue
                
                # 2. Identify Team Props
                is_team_prop = False
                
                # Check explicit types
                if curr_bet_type_lower in team_prop_types or curr_stat_type_lower in team_prop_types:
                    is_team_prop = True
                
                # Check for "Game Total" or similar in team names
                elif leg.player_team and 'game total' in leg.player_team.lower():
                    is_team_prop = True
                elif leg.player_name and 'game total' in leg.player_name.lower():
                    is_team_prop = True
                    
                # Check keywords if still unsure
                elif any(k in curr_bet_type_lower for k in team_prop_keywords):
                    # Be careful here, 'points' could be player points.
                    # 'total points' is usually game, 'points' is usually player.
                    if curr_bet_type_lower == 'total points' or 'game' in curr_bet_type_lower:
                        is_team_prop = True
                
                # 3. Assign New Values
                if is_team_prop:
                    new_bet_type = 'Team Prop'
                    # If stat_type is missing, try to use the old bet_type
                    if not new_stat_type or new_stat_type.lower() == 'team prop':
                        if curr_bet_type_lower not in ['team prop', 'team_prop']:
                            new_stat_type = original_bet_type
                        else:
                            new_stat_type = 'moneyline' # Default fallback? Or leave generic?
                else:
                    new_bet_type = 'Player Prop'
                    # If stat_type is missing, use the old bet_type
                    if not new_stat_type or new_stat_type.lower() == 'player prop':
                        if curr_bet_type_lower not in ['player prop', 'player_prop']:
                            new_stat_type = original_bet_type
                
                # 4. Apply Updates
                needs_save = False
                
                if leg.bet_type != new_bet_type:
                    leg.bet_type = new_bet_type
                    needs_save = True
                
                if leg.stat_type != new_stat_type:
                    leg.stat_type = new_stat_type
                    needs_save = True
                
                if needs_save:
                    updated_count += 1
                    logger.info(f"Fixed Leg {leg.id}: '{original_bet_type}' -> '{new_bet_type}' (Stat: '{new_stat_type}')")
            
            db.session.commit()
            logger.info(f"Fix complete. Updated {updated_count} legs.")
            
            # Final Verification Log
            results = db.session.query(BetLeg.bet_type, func.count(BetLeg.id)).group_by(BetLeg.bet_type).all()
            logger.info("Final Distribution:")
            for bt, c in results:
                logger.info(f"  '{bt}': {c}")

        except Exception as e:
            logger.error(f"Error during fix: {e}")
            db.session.rollback()

if __name__ == "__main__":
    fix_remaining_bet_types()
