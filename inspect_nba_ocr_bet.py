import logging
import os
import sys
from datetime import datetime, timedelta

# Set PROD DB URL
os.environ['DATABASE_URL'] = "postgresql://parlays_user:wgEpC1q34LIekYv6uelYqSThFdoy8xJT@dpg-d43b4iripnbc73bmuv5g-a.virginia-postgres.render.com/parlays"

from app import app, db
from models import Bet, BetLeg

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def inspect_nba_ocr_bet():
    with app.app_context():
        logger.info("\n--- Searching for Recent NBA Bets with Luka Doncic ---")
        
        # Search for legs with player "Luka Doncic"
        legs = BetLeg.query.filter(BetLeg.player_name.ilike("%Luka Doncic%")).order_by(BetLeg.created_at.desc()).limit(10).all()
        
        if not legs:
            logger.info("No legs found for Luka Doncic.")
            return

        for leg in legs:
            bet = leg.bet
            logger.info(f"\n--- Bet ID: {bet.id} (Site ID: {bet.betting_site_id}) ---")
            logger.info(f"Created At: {bet.created_at}")
            logger.info(f"Bet Status: {bet.status}")
            
            logger.info("Legs:")
            for l in bet.bet_legs_rel:
                logger.info(f"  - ID: {l.id}")
                logger.info(f"    Player: {l.player_name}")
                logger.info(f"    Team: {l.player_team}")
                logger.info(f"    Matchup: {l.away_team} @ {l.home_team}")
                logger.info(f"    Stat: {l.stat_type} {l.target_value}")
                logger.info(f"    Game ID: {l.game_id}")
                logger.info(f"    Status: {l.status}")
                
            # Check for multiple scoreboards (implied by different game IDs or something?)
            # The user said "3 live scoreboards were generated". This might mean the frontend grouped them into 3 games.
            # In the backend, this would manifest as legs having different game_ids or being associated with different games.
            
            game_ids = set(l.game_id for l in bet.bet_legs_rel)
            logger.info(f"Unique Game IDs in Bet: {game_ids}")

if __name__ == "__main__":
    inspect_nba_ocr_bet()
