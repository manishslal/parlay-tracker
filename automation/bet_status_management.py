"""
Bet Status Management Automation

Contains automations for managing bet status:
- auto_move_bets_no_live_legs: Moves bets to historical when no legs have live games
- auto_determine_leg_hit_status: Determines hit/miss status for completed bet legs
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def auto_move_bets_no_live_legs():
    """Automatically move bets to historical when no legs have games in progress.
    
    This checks all live bets and moves them to historical if none of their legs
    have games that are currently in progress (game_status != 'in_progress').
    
    This is different from auto_move_completed_bets which waits for games to be final.
    This moves bets as soon as their games are over, even if not yet STATUS_FINAL.
    """
    from app import app, db
    from models import Bet, BetLeg
    
    try:
        import logging
        logging.info("[AUTO-MOVE-NO-LIVE] Checking for bets with no live legs")
        
        # Get all live bets
        live_bets = Bet.query.filter_by(status='live', is_active=True).all()
        
        if not live_bets:
            logging.info("[AUTO-MOVE-NO-LIVE] No live bets found")
            return
        
        logging.info(f"[AUTO-MOVE-NO-LIVE] Checking {len(live_bets)} live bets")
        
        updated_count = 0
        
        for bet in live_bets:
            # Get bet legs from database
            bet_legs = BetLeg.query.filter(BetLeg.bet_id == bet.id).all()
            
            if not bet_legs:
                continue
            
            # Check if any leg has a game currently in progress or unknown status
            has_live_game = False
            has_unknown_status = False
            
            for leg in bet_legs:
                if leg.game_status in ['STATUS_IN_PROGRESS', 'STATUS_HALFTIME']:
                    has_live_game = True
                    break
                # If any leg has unknown status, we can't move yet
                if leg.game_status in ['unknown', 'STATUS_SCHEDULED']:
                    has_unknown_status = True
            
            # Only move to historical if:
            # 1. No legs have live games AND
            # 2. No legs have unknown or scheduled status (i.e., all games are definitively finished)
            if not has_live_game and not has_unknown_status:
                logging.info(f"[AUTO-MOVE-NO-LIVE] Bet {bet.id} has no live games - moving to historical")
                bet.is_active = False  # Move to historical
                bet.status = 'completed'  # Mark as completed
                bet.api_fetched = 'Yes'  # Stop fetching
                updated_count += 1
        
        # Commit all changes
        if updated_count > 0:
            db.session.commit()
            logging.info(f"[AUTO-MOVE-NO-LIVE] Moved {updated_count} bets to historical")
        else:
            logging.info("[AUTO-MOVE-NO-LIVE] No bets needed moving")
            
    except Exception as e:
        logging.error(f"[AUTO-MOVE-NO-LIVE] Error: {e}")
        db.session.rollback()


def auto_determine_leg_hit_status():
    """Automatically determine and set is_hit status for bet legs that have achieved_value but no is_hit.
    
    This processes all bet legs where:
    - achieved_value is not None (game data exists)
    - is_hit is None (hit/miss status not determined)
    
    Determines hit/miss based on bet type and compares achieved_value vs target_value.
    """
    from app import app, db
    from models import BetLeg
    
    try:
        import logging
        logging.info("[AUTO-HIT-STATUS] Checking for legs needing hit status determination")
        
        # Find all legs with achieved_value but no is_hit status AND game has finished
        legs_needing_status = BetLeg.query.filter(
            BetLeg.achieved_value.isnot(None),
            BetLeg.is_hit.is_(None),
            BetLeg.game_status == 'STATUS_FINAL'  # Only process finished games
        ).all()
        
        if not legs_needing_status:
            logging.info("[AUTO-HIT-STATUS] No legs need hit status determination")
            return
        
        logging.info(f"[AUTO-HIT-STATUS] Processing {len(legs_needing_status)} legs")
        
        updated_count = 0
        
        for leg in legs_needing_status:
            # Determine if the bet was hit based on bet type
            is_hit = False
            stat_type = leg.bet_type.lower() if leg.bet_type else ''
            
            if stat_type == 'moneyline':
                # Moneyline: won if score_diff > 0
                is_hit = leg.achieved_value > 0
            elif stat_type == 'spread':
                # Spread: won if (score_diff + spread) > 0
                if leg.target_value is not None:
                    is_hit = (leg.achieved_value + leg.target_value) > 0
            else:
                # Player props and other bets: compare achieved vs target
                if leg.target_value is not None:
                    # Check for over/under
                    if leg.bet_line_type == 'under':
                        is_hit = leg.achieved_value < leg.target_value
                    else:  # 'over' or None (default to over)
                        is_hit = leg.achieved_value >= leg.target_value
            
            # Update the leg
            leg.is_hit = is_hit
            # Also update status if it's still pending
            if leg.status == 'pending' or leg.status is None:
                leg.status = 'won' if is_hit else 'lost'
            
            logging.info(f"[AUTO-HIT-STATUS] Bet {leg.bet_id} Leg {leg.leg_order}: {leg.player_name} - {stat_type} - {'HIT' if is_hit else 'MISS'} (achieved: {leg.achieved_value}, target: {leg.target_value})")
            updated_count += 1
        
        # Commit all changes
        if updated_count > 0:
            db.session.commit()
            logging.info(f"[AUTO-HIT-STATUS] Updated hit status for {updated_count} legs")
        else:
            logging.info("[AUTO-HIT-STATUS] No legs were updated")
            
    except Exception as e:
        logging.error(f"[AUTO-HIT-STATUS] Error: {e}")
        db.session.rollback()
if __name__ == "__main__":
    # Allow running scripts standalone for testing
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "move_bets":
            auto_move_bets_no_live_legs()
        elif sys.argv[1] == "hit_status":
            auto_determine_leg_hit_status()
        else:
            print("Usage: python bet_status_management.py [move_bets|hit_status]")
    else:
        print("Running both automations...")
        auto_move_bets_no_live_legs()
        auto_determine_leg_hit_status()