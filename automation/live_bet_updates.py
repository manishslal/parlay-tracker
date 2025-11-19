"""
Live Bet Updates Automation

Contains automation for updating live/pending bets:
- update_live_bet_legs: Updates live bets every minute with current game data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def update_live_bet_legs():
    """Background job to update live bet legs with real-time ESPN data.
    
    Finds all live/pending bets and updates their legs with current game data:
    - Fetches live scores from ESPN API
    - Updates current values for active bets
    - Keeps live bets showing real-time data
    
    This runs every minute during active game times.
    """
    from app import app, db
    from models import Bet, BetLeg
    from app import process_parlay_data
    
    try:
        import logging
        logging.info("[LIVE-UPDATE] Starting live bet leg update check...")
        
        # Get all live and pending bets
        live_bets = Bet.query.filter(Bet.status.in_(['live', 'pending'])).all()
        
        if not live_bets:
            logging.info("[LIVE-UPDATE] No live/pending bets found")
            return
        
        logging.info(f"[LIVE-UPDATE] Updating {len(live_bets)} live/pending bets")
        
        updated_bets = 0
        updated_legs = 0
        
        for bet in live_bets:
            try:
                # Get bet data with live data fetching
                bet_data = bet.to_dict_structured(use_live_data=True)
                
                # Process the bet data to get live updates
                processed_bets = process_parlay_data([bet_data])
                
                if processed_bets and len(processed_bets) > 0:
                    processed_bet = processed_bets[0]
                    
                    # Get all bet legs ordered by leg_order
                    bet_legs = db.session.query(BetLeg).filter(
                        BetLeg.bet_id == bet.id
                    ).order_by(BetLeg.leg_order).all()
                    
                    # Update bet legs in database with live data
                    processed_legs = processed_bet.get('legs', [])
                    for i, leg_data in enumerate(processed_legs):
                        if i < len(bet_legs):
                            bet_leg = bet_legs[i]
                            
                            if 'current' in leg_data:
                                # Update current value if it changed
                                new_current = leg_data.get('current')
                                if new_current is not None and bet_leg.achieved_value != new_current:
                                    bet_leg.achieved_value = float(new_current)
                                    updated_legs += 1
                                    logging.debug(f"[LIVE-UPDATE] Bet {bet.id} Leg {bet_leg.leg_order}: achieved_value = {new_current}")
                                
                                # Update game status if available
                                if 'gameStatus' in leg_data and leg_data['gameStatus']:
                                    if bet_leg.game_status != leg_data['gameStatus']:
                                        bet_leg.game_status = leg_data['gameStatus']
                                        logging.debug(f"[LIVE-UPDATE] Bet {bet.id} Leg {bet_leg.leg_order}: game_status = {leg_data['gameStatus']}")
                                
                                # Update scores if available
                                if 'homeScore' in leg_data and leg_data['homeScore'] is not None:
                                    bet_leg.home_score = int(leg_data['homeScore'])
                                if 'awayScore' in leg_data and leg_data['awayScore'] is not None:
                                    bet_leg.away_score = int(leg_data['awayScore'])
                                
                                # Update game_id if available
                                if 'gameId' in leg_data and leg_data['gameId']:
                                    if bet_leg.game_id != leg_data['gameId']:
                                        bet_leg.game_id = leg_data['gameId']
                                        logging.debug(f"[LIVE-UPDATE] Bet {bet.id} Leg {bet_leg.leg_order}: game_id = {leg_data['gameId']}")
                    
                    updated_bets += 1
                    
            except Exception as e:
                logging.error(f"[LIVE-UPDATE] Error updating live bet {bet.id}: {e}")
                continue
        
        # Commit all changes
        db.session.commit()
        
        if updated_legs > 0:
            logging.info(f"[LIVE-UPDATE] ✓ Updated {updated_legs} legs across {updated_bets} live bets")
        else:
            logging.info("[LIVE-UPDATE] No live bet legs needed updating")
            
    except Exception as e:
        logging.error(f"[LIVE-UPDATE] Error in update_live_bet_legs: {e}")
        db.session.rollback()