
import sys
import os
import logging
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Production DB URL
PROD_DB_URL = "postgresql://parlays_user:wgEpC1q34LIekYv6uelYqSThFdoy8xJT@dpg-d43b4iripnbc73bmuv5g-a.virginia-postgres.render.com/parlays"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_prod_historical_team_props():
    logger.info("Connecting to PRODUCTION database...")
    
    try:
        engine = create_engine(PROD_DB_URL)
        Session = scoped_session(sessionmaker(bind=engine))
        session = Session()
        
        logger.info("Connected successfully.")
        
        # 1. Identify affected bets
        # Find historical bets with legs that are team props but have no achieved_value
        logger.info("Searching for affected bets...")
        
        # Using raw SQL for simplicity and to avoid model dependencies matching exactly
        query = text("""
            SELECT DISTINCT b.id
            FROM bets b
            JOIN bet_legs bl ON b.id = bl.bet_id
            WHERE b.is_active = false 
              AND b.is_archived = false
              AND (
                  lower(bl.bet_type) IN ('moneyline', 'spread', 'total', 'over_under', 'team_total', 'game_line')
                  OR lower(bl.stat_type) IN ('moneyline', 'spread', 'total_points', 'over_under', 'team_total_points', 'point_spread', 'total')
              )
              AND bl.achieved_value IS NULL
        """)
        
        result = session.execute(query)
        affected_bet_ids = [row[0] for row in result]
        
        if not affected_bet_ids:
            logger.info("No affected team prop legs found in PRODUCTION.")
            return

        logger.info(f"Found {len(affected_bet_ids)} affected bets in PRODUCTION.")
        
        # 2. Reset api_fetched flag
        update_query = text("""
            UPDATE bets
            SET api_fetched = 'No'
            WHERE id IN :bet_ids
        """)
        
        session.execute(update_query, {'bet_ids': tuple(affected_bet_ids)})
        session.commit()
        
        logger.info(f"Successfully reset {len(affected_bet_ids)} bets for reprocessing.")
        logger.info("NOTE: The actual reprocessing will happen when the automation job runs on the production server.")
        logger.info("If you want to force it now, you would need to run the automation code against this DB.")
        
        # Optional: We could try to run the automation logic here, but it requires the full app context
        # and might be risky/complex to set up remotely if dependencies differ.
        # Resetting the flag is the safest first step. The production scheduler should pick it up.
        
    except Exception as e:
        logger.error(f"Error running fix on PRODUCTION: {e}")
    finally:
        if 'session' in locals():
            session.close()

if __name__ == "__main__":
    fix_prod_historical_team_props()
