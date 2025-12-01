import logging
import os
import sys

# Set PROD DB URL
os.environ['DATABASE_URL'] = "postgresql://parlays_user:wgEpC1q34LIekYv6uelYqSThFdoy8xJT@dpg-d43b4iripnbc73bmuv5g-a.virginia-postgres.render.com/parlays"

from app import app, db
from models import Bet
from helpers.utils import _get_touchdowns, _get_player_stat_from_boxscore
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_live_bet():
    target_id = 177
    
    with app.app_context():
        logger.info(f"\n--- Inspecting Live Bet ID: {target_id} ---")
        bet = Bet.query.get(target_id)
        
        if not bet:
            logger.error("Bet not found!")
            return

        for leg in bet.bet_legs_rel:
            if 'touchdown' in leg.stat_type.lower():
                logger.info(f"\n--- Inspecting Leg {leg.id} ({leg.player_name}) ---")
                
                # Fetch game summary from ESPN
                url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={leg.game_id}"
                logger.info(f"Fetching ESPN Summary: {url}")
                try:
                    data = requests.get(url).json()
                    # _get_player_stat_from_boxscore expects the 'players' list, not the full boxscore dict
                    boxscore = data.get('boxscore', {}).get('players', [])
                    scoring_plays = data.get('scoring_plays', [])
                    
                    # Simulate _get_touchdowns logic
                    logger.info("Simulating _get_touchdowns...")
                    
                    td_cats = {
                        "rushing": "TD", "receiving": "TD",
                        "interception": "TD", "kickoffReturn": "TD", "puntReturn": "TD",
                        "fumbleReturn": "TD"
                    }
                    total_tds = 0
                    for cat, label in td_cats.items():
                        val = _get_player_stat_from_boxscore(leg.player_name, cat, label, boxscore)
                        logger.info(f"  Cat '{cat}' Label '{label}': {val}")
                        if val is not None:
                            total_tds += val
                            
                    logger.info(f"  Total TDs (Sum): {total_tds}")
                    
                    # Check scoring plays fallback
                    if total_tds == 0:
                        logger.info("  Checking scoring plays fallback...")
                        # ... (scoring plays logic simulation if needed)
                        
                except Exception as e:
                    logger.error(f"Error fetching/parsing ESPN data: {e}")

if __name__ == "__main__":
    debug_live_bet()
