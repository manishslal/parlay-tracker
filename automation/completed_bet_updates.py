"""
Completed Bet Updates Automation

Contains automation for updating completed bets with final results:
- update_completed_bet_legs: Updates bets with STATUS_FINAL games
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def update_completed_bet_legs():
    """Update bet legs for completed games (STATUS_FINAL).
    
    This function processes all bet legs where the game has finished (STATUS_FINAL)
    and updates the achieved_value based on the bet type and game results.
    """
    from app import app, db
    from models import BetLeg
    from app import process_parlay_data
    
    try:
        import logging
        logging.info("[COMPLETED-UPDATES] Starting update of completed bet legs")
        
        # Get all bet legs with STATUS_FINAL games that haven't been processed yet
        # (achieved_value is None indicates it hasn't been processed)
        legs_to_update = BetLeg.query.filter(
            BetLeg.game_status == 'STATUS_FINAL',
            BetLeg.achieved_value.is_(None)
        ).all()
        
        if not legs_to_update:
            logging.info("[COMPLETED-UPDATES] No completed bet legs to update")
            return
        
        logging.info(f"[COMPLETED-UPDATES] Processing {len(legs_to_update)} completed bet legs")
        
        updated_count = 0
        
        for leg in legs_to_update:
            try:
                # Get the bet for this leg
                from models import Bet
                bet = Bet.query.filter_by(id=leg.bet_id).first()
                if not bet:
                    logging.warning(f"[COMPLETED-UPDATES] Bet {leg.bet_id} not found for leg {leg.id}")
                    continue
                
                # Convert bet to dictionary format expected by process_parlay_data
                bet_data = bet.to_dict_structured(use_live_data=True)
                
                # Process the bet data to get final results
                processed_bets = process_parlay_data([bet_data])
                
                if processed_bets and len(processed_bets) > 0:
                    processed_bet = processed_bets[0]
                    processed_legs = processed_bet.get('legs', [])
                    
                    # Find the matching leg in processed data
                    for processed_leg in processed_legs:
                        if (processed_leg.get('leg_order') == leg.leg_order or 
                            processed_leg.get('player') == leg.player_name):
                            achieved_value = processed_leg.get('current')
                            if achieved_value is not None:
                                leg.achieved_value = achieved_value
                                logging.info(f"[COMPLETED-UPDATES] Updated bet {leg.bet_id} leg {leg.leg_order}: achieved_value = {achieved_value}")
                                updated_count += 1
                            break
                
            except Exception as e:
                logging.error(f"[COMPLETED-UPDATES] Error processing bet {leg.bet_id} leg {leg.leg_order}: {e}")
                continue
        
        # Commit all changes
        if updated_count > 0:
            db.session.commit()
            logging.info(f"[COMPLETED-UPDATES] Successfully updated {updated_count} completed bet legs")
        else:
            logging.info("[COMPLETED-UPDATES] No bet legs were updated")
            
    except Exception as e:
        logging.error(f"[COMPLETED-UPDATES] Error: {e}")
        db.session.rollback()