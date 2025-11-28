import logging
import os

# Set PROD DB URL - REMOVED FOR SECURITY
# os.environ['DATABASE_URL'] = "..." 

from app import app, db
from models import Bet, BetLeg

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def repair_historical_bets():
    """
    Reset api_fetched status for historical bets that have missing stats.
    This will trigger the historical bet processing job to re-fetch data.
    """
    with app.app_context():
        logger.info("Starting repair of historical bets...")
        
        # Find bets that are marked as fetched but have legs with no achieved value
        # or 0 achieved value (which might be incorrect for some stats)
        # We'll be conservative and look for NULL achieved values first
        
        # Find all bets that are completed but have missing stats or haven't been fetched
        broken_bets = db.session.query(Bet).join(BetLeg).filter(
            Bet.status.in_(['completed', 'lost', 'won']),
            (Bet.api_fetched != 'Yes') | (BetLeg.achieved_value.is_(None)) | (BetLeg.achieved_value == 0)
        ).distinct().all()
        
        # Explicitly add bets 178, 179, and 177 (Anytime TD fix) if they exist
        for target_id in [178, 179, 177]:
            bet = Bet.query.get(target_id)
            if bet:
                if bet not in broken_bets:
                    broken_bets.append(bet)
                logger.info(f"Targeting specific bet {target_id} for repair")
            else:
                logger.warning(f"Target bet {target_id} not found")
        
        logger.info(f"Found {len(broken_bets)} total bets to repair.")
        
        count = 0
        for bet in broken_bets:
            # Only reset if it looks like a historical bet (not a fresh live one)
            # We assume anything completed/lost/won is historical or should be
            logger.info(f"Resetting bet {bet.id} (Site ID: {bet.betting_site_id})")
            bet.api_fetched = 'No'
            bet.is_active = False
            bet.is_archived = False
            count += 1
            
        # Also check for bets with 0 achieved value where it might be suspicious?
        # For now, let's stick to NULLs as that's the clear symptom of the bug.
        
        if count > 0:
            db.session.commit()
            logger.info(f"Successfully reset {count} bets. They will be processed by the next scheduled job.")
            
            # Trigger processing immediately?
            # We can import and run the function
            try:
                from automation.historical_bet_processing import process_historical_bets_api
                logger.info("Triggering immediate processing...")
                process_historical_bets_api()
            except Exception as e:
                logger.error(f"Failed to trigger immediate processing: {e}")
        else:
            logger.info("No bets needed repair.")

if __name__ == "__main__":
    repair_historical_bets()
