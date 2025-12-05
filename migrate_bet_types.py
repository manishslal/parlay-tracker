
import sys
import os
import logging
from sqlalchemy import or_

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add current directory to path
sys.path.append(os.getcwd())

from app import app, db
from models import BetLeg

def migrate_bet_types():
    """
    Migrate existing BetLeg records to standardize bet_type to 'Player Prop' or 'Team Prop'.
    Moves specific types (moneyline, spread, etc.) to stat_type.
    """
    with app.app_context():
        try:
            logger.info("Starting bet type migration...")
            
            # Get all bet legs
            legs = BetLeg.query.all()
            logger.info(f"Found {len(legs)} legs to process")
            
            updated_count = 0
            
            for leg in legs:
                original_bet_type = leg.bet_type
                original_stat_type = leg.stat_type
                
                new_bet_type = None
                new_stat_type = None
                
                # Determine if it's a Team Prop or Player Prop
                # List of types that are definitely Team Props
                team_prop_types = [
                    'moneyline', 'spread', 'total_points', 'over_under', 
                    'team_total', 'total', 'game_line', 'game_total'
                ]
                
                # Check current bet_type
                if original_bet_type and original_bet_type.lower() in team_prop_types:
                    new_bet_type = 'Team Prop'
                    # If stat_type is missing or generic, use the bet_type
                    if not original_stat_type or original_stat_type.lower() == 'team_prop':
                        new_stat_type = original_bet_type.lower()
                    else:
                        new_stat_type = original_stat_type
                
                # Check current stat_type (sometimes bet_type is generic 'Team Prop' already)
                elif original_stat_type and original_stat_type.lower() in team_prop_types:
                    new_bet_type = 'Team Prop'
                    new_stat_type = original_stat_type.lower()
                    
                # Default to Player Prop if not identified as Team Prop
                else:
                    new_bet_type = 'Player Prop'
                    # If bet_type was something specific like 'points', move it to stat_type
                    if original_bet_type and original_bet_type.lower() not in ['player_prop', 'player prop']:
                        new_stat_type = original_bet_type.lower()
                    else:
                        new_stat_type = original_stat_type if original_stat_type else 'unknown'

                # Apply updates if changed
                needs_update = False
                if leg.bet_type != new_bet_type:
                    leg.bet_type = new_bet_type
                    needs_update = True
                
                if leg.stat_type != new_stat_type:
                    leg.stat_type = new_stat_type
                    needs_update = True
                    
                if needs_update:
                    updated_count += 1
                    # logger.info(f"Updated Leg {leg.id}: {original_bet_type}/{original_stat_type} -> {new_bet_type}/{new_stat_type}")
            
            db.session.commit()
            logger.info(f"Migration complete. Updated {updated_count} legs.")
            
        except Exception as e:
            logger.error(f"Error during migration: {e}")
            db.session.rollback()

if __name__ == "__main__":
    migrate_bet_types()
