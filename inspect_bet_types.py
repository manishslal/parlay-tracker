
import sys
import os
import logging
from sqlalchemy import func

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add current directory to path
sys.path.append(os.getcwd())

from app import app, db
from models import BetLeg

def inspect_bet_types():
    """
    Inspect the distribution of bet_type in the bet_legs table.
    """
    with app.app_context():
        try:
            # Query for total legs
            total_legs = BetLeg.query.count()
            print(f"\nTotal Bet Legs in DB: {total_legs}")

            # Query for distinct bet_types and their counts
            results = db.session.query(BetLeg.bet_type, func.count(BetLeg.id)).group_by(BetLeg.bet_type).all()
            
            print("\n--- Current Bet Type Distribution ---")
            if not results:
                print("No results found from group_by query.")
            
            for bet_type, count in results:
                print(f"'{bet_type}': {count}")
            
            # Identify non-standard types (exact match check)
            non_standard = [r for r in results if r[0] not in ['Player Prop', 'Team Prop']]
            
            if non_standard:
                print("\n--- Non-Standard Bet Types Found ---")
                for bet_type, count in non_standard:
                    print(f"'{bet_type}': {count}")
                    
                    # Show a sample leg for context
                    sample = BetLeg.query.filter_by(bet_type=bet_type).first()
                    if sample:
                        print(f"  Sample Leg ID: {sample.id}")
                        print(f"  Player: {sample.player_name}")
                        print(f"  Team: {sample.player_team}")
                        print(f"  Stat Type: {sample.stat_type}")
                        print(f"  Home/Away: {sample.home_team} vs {sample.away_team}")
                        print("-" * 30)
            elif total_legs > 0:
                print("\nAll bet legs are standardized!")
            else:
                print("\nNo bet legs found to inspect.")

        except Exception as e:
            logger.error(f"Error inspecting bet types: {e}")

if __name__ == "__main__":
    inspect_bet_types()
