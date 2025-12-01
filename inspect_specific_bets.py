from app import app, db
from models import Bet, BetLeg
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def inspect_specific_bets():
    with app.app_context():
        logger.info("\n--- Inspecting Bet 45 (Empty Site ID) ---")
        bet = Bet.query.get(45)
        if bet:
            logger.info(f"ID: {bet.id}")
            logger.info(f"Site ID Column: '{bet.betting_site_id}'")
            logger.info(f"Bet Data: {bet.bet_data}")
        else:
            logger.error("Bet 45 not found.")

if __name__ == "__main__":
    inspect_specific_bets()
