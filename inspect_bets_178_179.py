from app import app, db
from models import Bet, BetLeg
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def inspect_bets():
    target_ids = [178, 179]
    
    with app.app_context():
        for bet_id in target_ids:
            logger.info(f"\n--- Inspecting Bet ID: {bet_id} ---")
            bet = Bet.query.get(bet_id)
            
            if not bet:
                logger.error(f"Bet {bet_id} not found!")
                continue
                
            logger.info(f"Status: {bet.status}")
            logger.info(f"Active: {bet.is_active}")
            logger.info(f"Archived: {bet.is_archived}")
            logger.info(f"API Fetched: {bet.api_fetched}")
            logger.info(f"Created At: {bet.created_at}")
            
            legs = bet.bet_legs_rel
            for leg in legs:
                logger.info(f"  Leg {leg.id}:")
                logger.info(f"    Player: {leg.player_name} (ID: {leg.player_id})")
                logger.info(f"    Stat: {leg.stat_type} {leg.bet_line_type} {leg.target_value}")
                logger.info(f"    Achieved: {leg.achieved_value}")
                logger.info(f"    Game ID: {leg.game_id}")
                logger.info(f"    Game Status: {leg.game_status}")
                logger.info(f"    Status: {leg.status}")
                logger.info(f"    Scores: {leg.home_score} - {leg.away_score}")

if __name__ == "__main__":
    inspect_bets()
