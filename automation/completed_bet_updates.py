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
        # Use with_for_update() to lock rows and prevent race conditions
        legs_to_update = BetLeg.query.filter(
            BetLeg.game_status == 'STATUS_FINAL',
            BetLeg.achieved_value.is_(None)
        ).with_for_update().all()
        
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
                    
                    # Find the matching leg in processed data using composite key
                    # Priority: leg_order (most reliable) > (player_name + stat_type) composite
                    for processed_leg in processed_legs:
                        # Try matching by leg_order first (most reliable)
                        if processed_leg.get('leg_order') == leg.leg_order:
                            # Double-check player and stat match if available
                            proc_player = processed_leg.get('player', '')
                            proc_stat = processed_leg.get('stat', '')
                            
                            # If player/stat provided, verify they match
                            if proc_player and leg.player_name:
                                if proc_player.lower() not in leg.player_name.lower() and leg.player_name.lower() not in proc_player.lower():
                                    logging.warning(f"[COMPLETED-UPDATES] Leg {leg.leg_order} matched by order but player mismatch: '{leg.player_name}' vs '{proc_player}'")
                                    continue
                            
                            if proc_stat and leg.stat_type:
                                if proc_stat.lower() != leg.stat_type.lower():
                                    logging.warning(f"[COMPLETED-UPDATES] Leg {leg.leg_order} matched by order but stat mismatch: '{leg.stat_type}' vs '{proc_stat}'")
                                    continue
                            
                            achieved_value = processed_leg.get('current')
                            if achieved_value is not None:
                                # Validate the value before updating
                                from automation.validators import validate_achieved_value, log_validation_failure
                                is_valid, reason = validate_achieved_value(
                                    leg.stat_type,
                                    achieved_value,
                                    leg.player_name
                                )
                                
                                if is_valid:
                                    old_val = leg.achieved_value
                                    leg.achieved_value = achieved_value
                                    
                                    # Audit log the value update
                                    from helpers.audit_helpers import log_leg_value_update
                                    log_leg_value_update(
                                        db_session=db.session,
                                        bet_id=leg.bet_id,
                                        leg_id=leg.id,
                                        player_name=leg.player_name,
                                        stat_type=leg.stat_type,
                                        old_value=old_val,
                                        new_value=achieved_value,
                                        automation_name='completed_bet_updates'
                                    )
                                    
                                    logging.info(f"[COMPLETED-UPDATES] Updated bet {leg.bet_id} leg {leg.leg_order}: {leg.player_name} {leg.stat_type} = {achieved_value}")
                                    updated_count += 1
                                else:
                                    log_validation_failure(
                                        "[COMPLETED-UPDATES]",
                                        reason,
                                        bet_id=leg.bet_id,
                                        leg_order=leg.leg_order,
                                        player=leg.player_name,
                                        stat=leg.stat_type,
                                        proposed_value=achieved_value
                                    )
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