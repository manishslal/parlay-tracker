import logging
import os
import sys

# Set PROD DB URL
os.environ['DATABASE_URL'] = "postgresql://parlays_user:wgEpC1q34LIekYv6uelYqSThFdoy8xJT@dpg-d43b4iripnbc73bmuv5g-a.virginia-postgres.render.com/parlays"

from app import app, db
from models import Bet, BetLeg
from helpers.espn_api import get_espn_games_with_ids_for_date, _get_player_stats_from_boxscore, _extract_achieved_value
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_anytime_td():
    target_site_id = 'O/0851945/0000001'
    
    with app.app_context():
        logger.info(f"\n--- Searching for Bet: {target_site_id} ---")
        bet = Bet.query.filter_by(betting_site_id=target_site_id).first()
        
        if not bet:
            logger.info("Exact match failed, trying partial match...")
            bet = Bet.query.filter(Bet.betting_site_id.ilike(f"%{target_site_id}%")).first()
            
        if not bet:
            logger.error("Bet not found!")
            return

        logger.info(f"Found Bet ID: {bet.id} (Site ID: {bet.betting_site_id})")
        
        for leg in bet.bet_legs_rel:
            if 'touchdown' in leg.stat_type.lower() or 'td' in leg.stat_type.lower() or 'anytime' in leg.stat_type.lower():
                logger.info(f"\n--- Inspecting TD Leg {leg.id} ---")
                logger.info(f"Player: {leg.player_name}")
                logger.info(f"Stat Type: {leg.stat_type}")
                logger.info(f"Achieved Value (DB): {leg.achieved_value}")
                logger.info(f"Game ID: {leg.game_id}")
                
                if not leg.game_id:
                    logger.warning("No Game ID found for leg!")
                    continue
                    
                # Fetch game summary from ESPN
                url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={leg.game_id}"
                logger.info(f"Fetching ESPN Summary: {url}")
                try:
                    data = requests.get(url).json()
                    boxscore = data.get('boxscore', {})
                    
                    # 1. Test _get_player_stats_from_boxscore
                    stats = _get_player_stats_from_boxscore(leg.player_name, 'NFL', boxscore)
                    logger.info(f"Extracted Stats: {stats}")
                    
                    # 2. Test _extract_achieved_value
                    # Mock a leg dict for the function
                    leg_dict = {
                        'stat': leg.stat_type,
                        'target': leg.target_value
                    }
                    achieved = _extract_achieved_value(stats, leg.stat_type, leg.bet_type, leg.bet_line_type)
                    logger.info(f"Calculated Achieved Value: {achieved}")
                    
                    # 3. Manually check for TDs in stats
                    td_keys = [k for k in stats.keys() if 'td' in k.lower()]
                    logger.info(f"TD Keys in Stats: {td_keys}")
                    total_tds = sum(float(stats.get(k, 0)) for k in td_keys)
                    logger.info(f"Manual Total TDs Sum: {total_tds}")
                    
                except Exception as e:
                    logger.error(f"Error fetching/parsing ESPN data: {e}")

if __name__ == "__main__":
    debug_anytime_td()
