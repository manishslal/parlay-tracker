import logging
import os
import sys
from datetime import datetime

# Set PROD DB URL
os.environ['DATABASE_URL'] = "postgresql://parlays_user:wgEpC1q34LIekYv6uelYqSThFdoy8xJT@dpg-d43b4iripnbc73bmuv5g-a.virginia-postgres.render.com/parlays"

from app import app, db
from models import Bet, BetLeg

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_nba_ocr_bet():
    target_bet_id = 183
    correct_game_id = "401810163"
    correct_home_team = "Los Angeles Lakers"
    correct_away_team = "New Orleans Pelicans"
    correct_player_team = "Lakers"
    
    with app.app_context():
        logger.info(f"\n--- Fixing Bet ID: {target_bet_id} ---")
        bet = Bet.query.get(target_bet_id)
        
        if not bet:
            logger.error("Bet not found!")
            return

        for leg in bet.bet_legs_rel:
            logger.info(f"Processing Leg {leg.id} ({leg.player_name})")
            
            # Update Game Details for ALL legs to unify the scoreboard
            if leg.game_id != correct_game_id or leg.home_team != correct_home_team:
                logger.info(f"  Updating Game ID from {leg.game_id} to {correct_game_id}")
                leg.game_id = correct_game_id
                leg.home_team = correct_home_team
                leg.away_team = correct_away_team
                # Ensure game_date is set (taking from bet creation if missing, or just rely on existing)
                if not leg.game_date:
                     leg.game_date = bet.created_at.date()

            # Fix Luka Doncic's Team
            if "Luka Doncic" in leg.player_name:
                if leg.player_team != correct_player_team:
                    logger.info(f"  Updating Player Team from {leg.player_team} to {correct_player_team}")
                    leg.player_team = correct_player_team
            
            # Fix other Lakers players if their team is wrong (though they seemed fine)
            if leg.player_name in ["LeBron James", "Austin Reaves", "Anthony Davis"]:
                 if leg.player_team != correct_player_team:
                    logger.info(f"  Updating Player Team from {leg.player_team} to {correct_player_team}")
                    leg.player_team = correct_player_team

        try:
            db.session.commit()
            logger.info("Successfully committed changes.")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error committing changes: {e}")

if __name__ == "__main__":
    fix_nba_ocr_bet()
