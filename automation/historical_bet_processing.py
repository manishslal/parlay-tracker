"""
Historical Bet Processing Automation

Processes historical bets that haven't been fetched from ESPN API yet.
Fills in missing player data, fetches ESPN game data, and updates bet status.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

def process_historical_bets_api():
    """
    Process historical bets that haven't been fetched from ESPN API yet.
    
    For each historical bet where api_fetched is blank:
    1. Link players to bet_legs by matching player names
    2. Fetch ESPN data for each leg
    3. Update bet_legs with achieved values and game results
    4. Mark bet as api_fetched = 'Yes' when complete
    
    Any failures are logged to the Issues page.
    """
    from app import app, db
    from models import Bet, BetLeg, Player
    
    with app.app_context():
        try:
            logger.info("[HISTORICAL-API] Starting historical bet API processing")
            
            # Get all historical bets that haven't been API fetched
            historical_bets = Bet.query.filter_by(
                is_active=False, 
                is_archived=False,
                api_fetched='No'
            ).options(db.joinedload(Bet.bet_legs_rel)).all()
            
            if not historical_bets:
                logger.info("[HISTORICAL-API] No historical bets need API processing")
                return
            
            logger.info(f"[HISTORICAL-API] Processing {len(historical_bets)} historical bets")
            
            processed_count = 0
            issues = []
            
            for bet in historical_bets:
                try:
                    logger.info(f"[HISTORICAL-API] Processing bet {bet.id}")
                    
                    # Get bet legs
                    bet_legs = bet.bet_legs_rel
                    if not bet_legs:
                        issues.append(f"Bet {bet.id}: No legs found")
                        continue
                    
                    # Process each leg
                    all_legs_processed = True
                    for leg in bet_legs:
                        try:
                            # Step 3a: Link player to bet_leg
                            if not _link_player_to_leg(leg, db, issues):
                                all_legs_processed = False
                                continue
                            
                            # Step 3d: Fetch ESPN data for the leg
                            if not _fetch_espn_data_for_leg(leg, issues):
                                all_legs_processed = False
                                continue
                            
                            # Step 3e: Set game status and hit status
                            _update_leg_status(leg)
                            
                        except Exception as e:
                            logger.error(f"[HISTORICAL-API] Error processing leg {leg.id} in bet {bet.id}: {e}")
                            issues.append(f"Bet {bet.id}, Leg {leg.id}: Processing error - {str(e)}")
                            all_legs_processed = False
                    
                    # Step 3f: If all legs processed successfully, mark bet as complete
                    if all_legs_processed:
                        bet.api_fetched = 'Yes'
                        bet.last_api_update = datetime.now(timezone.utc)
                        processed_count += 1
                        
                        # Step 3g: Update bet status based on leg statuses
                        _update_bet_status_from_legs(bet)
                        _update_bet_stats_from_legs(bet)
                        
                        # Step 3h: Check if any legs are live - if so, revert bet to is_active=True
                        has_live_legs = any(leg.status == 'live' for leg in bet.bet_legs_rel)
                        if has_live_legs:
                            bet.is_active = True
                            logger.info(f"[HISTORICAL-API] Bet {bet.id} has live legs - reverting to is_active=True, status={bet.status}")
                        
                        logger.info(f"[HISTORICAL-API] Successfully processed bet {bet.id}")
                    else:
                        logger.warning(f"[HISTORICAL-API] Bet {bet.id} had processing issues")
                        
                except Exception as e:
                    logger.error(f"[HISTORICAL-API] Error processing bet {bet.id}: {e}")
                    issues.append(f"Bet {bet.id}: General processing error - {str(e)}")
            
            # Commit all changes
            db.session.commit()
            
            # Log issues to the Issues page
            if issues:
                _log_issues_to_page(issues)
            
            logger.info(f"[HISTORICAL-API] Completed processing {processed_count} bets with {len(issues)} issues")
            
        except Exception as e:
            logger.error(f"[HISTORICAL-API] Fatal error: {e}")
            db.session.rollback()


def _link_player_to_leg(leg, db, issues):
    """
    Step 3a: Link player to bet_leg by matching names.
    
    Returns True if successful, False otherwise.
    
    Note: Team prop bets (moneyline, spread, total_points) should NOT have player_ids.
    Only player prop bets (player_prop, passing_yards, etc.) should be linked.
    """
    from models import Player
    
    # Skip team prop bets - these don't need player linking
    # Team props have stat_type in: moneyline, spread, total_points
    if leg.stat_type and leg.stat_type.lower() in ['moneyline', 'spread', 'total_points']:
        logger.debug(f"[HISTORICAL-API] Skipping team prop leg {leg.id} (stat_type={leg.stat_type}) - no player linking needed")
        return True  # Success, but no linking needed
    
    if not leg.player_name:
        return True  # Not a player bet, no linking needed
    
    # Try to find player by exact name matches
    player = Player.query.filter(
        db.or_(
            Player.player_name == leg.player_name,
            Player.normalized_name == leg.player_name,
            Player.display_name == leg.player_name
        ),
        Player.sport == leg.sport
    ).first()
    
    if player:
        leg.player_id = player.id
        leg.position = player.position  # Step 3c
        logger.debug(f"[HISTORICAL-API] Linked player {player.player_name} (ID: {player.id}) to leg {leg.id}")
        return True
    else:
        issues.append(f"Bet {leg.bet_id}, Leg {leg.id}: No player match found for '{leg.player_name}' ({leg.sport})")
        return False


def _fetch_espn_data_for_leg(leg, issues):
    """
    Step 3d: Fetch comprehensive ESPN data for the leg.
    
    Updates: achieved_value, home_score, away_score, is_home_game, game_id, game_status
    """
    try:
        # Import ESPN helper functions
        from helpers import espn_api
        from datetime import datetime
        
        # Get game data from ESPN
        game_data = espn_api.get_espn_game_data(
            leg.home_team, 
            leg.away_team, 
            leg.game_date.strftime('%Y-%m-%d') if hasattr(leg.game_date, 'strftime') else str(leg.game_date),
            player_name=leg.player_name if leg.player_name else None,
            sport=leg.sport,
            stat_type=leg.stat_type,
            bet_type=leg.bet_type,
            bet_line_type=leg.bet_line_type
        )
        
        if not game_data:
            issues.append(f"Bet {leg.bet_id}, Leg {leg.id}: No ESPN data found for {leg.away_team} @ {leg.home_team} on {leg.game_date}")
            return False
        
        # Update leg with ESPN data
        leg.achieved_value = game_data.get('achieved_value')
        leg.home_score = game_data.get('home_score')
        leg.away_score = game_data.get('away_score')
        leg.is_home_game = game_data.get('is_home_game')
        leg.game_id = game_data.get('game_id')
        leg.game_status = game_data.get('game_status', 'STATUS_END_PERIOD')  # Store the actual game status from ESPN
        
        logger.debug(f"[HISTORICAL-API] Updated leg {leg.id} with ESPN data: achieved={leg.achieved_value}, scores={leg.home_score}-{leg.away_score}, game_status={leg.game_status}")
        return True
        
    except Exception as e:
        logger.error(f"[HISTORICAL-API] ESPN fetch error for leg {leg.id}: {e}")
        issues.append(f"Bet {leg.bet_id}, Leg {leg.id}: ESPN API error - {str(e)}")
        return False


def _update_leg_status(leg):
    """
    Step 3e: Set status and is_hit based on game_status and achieved data.
    Only mark as won/lost if game is actually finished (STATUS_FINAL).
    """
    # Check if game is finished
    is_game_finished = leg.game_status == 'STATUS_FINAL'
    
    # Determine if the bet was hit (only if game is finished and we have data)
    if is_game_finished and leg.achieved_value is not None and leg.target_value is not None:
        stat_type = leg.bet_type.lower()
        
        # SAFEGUARD: Ensure values are numbers
        achieved = float(leg.achieved_value)
        target = float(leg.target_value)
        
        if stat_type == 'moneyline':
            leg.is_hit = achieved > 0
        elif stat_type == 'spread':
            leg.is_hit = (achieved + target) > 0
        elif stat_type in ['total_points', 'player_prop', 'total', 'made_threes', 'assists', 'points']:
            if leg.bet_line_type == 'under':
                leg.is_hit = achieved < target
            else:  # over
                leg.is_hit = achieved >= target
        else:
            leg.is_hit = False  # Default to not hit
        
        leg.status = 'won' if leg.is_hit else 'lost'
    elif is_game_finished and leg.achieved_value is None:
        # Game finished but we don't have player stats
        leg.status = 'pending'
        leg.is_hit = None
    else:
        # Game not finished yet - mark as live
        leg.status = 'live'
        leg.is_hit = None


def _update_bet_status_from_legs(bet):
    """
    Update bet status based on its legs' statuses.
    Bet status should reflect the most critical leg status.
    """
    if not bet.bet_legs_rel:
        return
    
    leg_statuses = [leg.status for leg in bet.bet_legs_rel]
    
    # Priority: live > pending > won/lost
    if 'live' in leg_statuses:
        bet.status = 'live'
    elif 'pending' in leg_statuses:
        bet.status = 'pending'
    elif all(status in ['won', 'lost'] for status in leg_statuses):
        # All legs are finished - determine won/lost
        if all(status == 'won' for status in leg_statuses):
            bet.status = 'won'
        elif any(status == 'lost' for status in leg_statuses):
            bet.status = 'lost'
        else:
            # Should not happen if logic is correct
            bet.status = 'completed'
    else:
        # Mixed - if any are won/lost, mark as completed (should be unreachable if logic above is correct)
        bet.status = 'completed'


def _update_bet_stats_from_legs(bet):
    """
    Update bet's leg count statistics from its legs.
    """
    legs = bet.bet_legs_rel
    if not legs:
        return
    
    bet.total_legs = len(legs)
    bet.legs_won = sum(1 for leg in legs if leg.status == 'won')
    bet.legs_lost = sum(1 for leg in legs if leg.status == 'lost')
    bet.legs_pending = sum(1 for leg in legs if leg.status == 'pending')
    bet.legs_live = sum(1 for leg in legs if leg.status == 'live')


def _log_issues_to_page(issues: List[str]):
    """
    Log issues to the Issues page for user review.
    """
    try:
        # For now, just log to the application logger
        # In the future, this could write to a database table
        for issue in issues:
            logger.warning(f"[ISSUES] {issue}")
        
        logger.info(f"[ISSUES] Logged {len(issues)} issues to tracking page")
        
    except Exception as e:
        logger.error(f"[ISSUES] Error logging issues: {e}")