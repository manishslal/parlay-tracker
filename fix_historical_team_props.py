
import sys
import os
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Bet, BetLeg
from automation.historical_bet_processing import process_historical_bets_api

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_historical_team_props():
    with app.app_context():
        logger.info("Starting retroactive fix for historical team props...")
        
        # 1. Identify affected bets
        # Find historical bets with legs that are team props but have no achieved_value
        team_prop_types = ['moneyline', 'spread', 'total', 'over_under', 'team_total', 'game_line']
        team_prop_stats = ['moneyline', 'spread', 'total_points', 'over_under', 'team_total_points', 'point_spread', 'total']
        
        affected_legs = BetLeg.query.join(Bet).filter(
            Bet.is_active == False,  # Historical
            Bet.is_archived == False,
            db.or_(
                BetLeg.bet_type.in_(team_prop_types),
                BetLeg.stat_type.in_(team_prop_stats)
            ),
            BetLeg.achieved_value.is_(None)
        ).all()
        
        if not affected_legs:
            logger.info("No affected team prop legs found.")
            return

        affected_bet_ids = set(leg.bet_id for leg in affected_legs)
        logger.info(f"Found {len(affected_legs)} affected legs across {len(affected_bet_ids)} bets.")
        
        # 2. Reset api_fetched flag
        bets_to_update = Bet.query.filter(Bet.id.in_(affected_bet_ids)).all()
        
        for bet in bets_to_update:
            bet.api_fetched = 'No'
            logger.info(f"Resetting api_fetched for Bet {bet.id}")
            
        db.session.commit()
        logger.info(f"Successfully reset {len(bets_to_update)} bets for reprocessing.")
        
        # 3. Trigger reprocessing
        logger.info("Triggering historical bet processing...")
        process_historical_bets_api()
        logger.info("Processing complete.")

if __name__ == "__main__":
    fix_historical_team_props()
