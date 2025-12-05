"""
database.py - Migration and DB setup utilities for Parlay Tracker
"""
from models import db, User
from sqlalchemy import inspect

def run_migrations_once(app):
    """
    Run startup migrations to ensure DB schema is up to date.
    Adds user_role column if missing and sets admin user.
    """
    with app.app_context():
        try:
            # Ensure all tables are created
            db.create_all()
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            if 'user_role' not in columns:
                print("[MIGRATION] Adding user_role column...")
                db.session.execute(db.text("ALTER TABLE users ADD COLUMN user_role VARCHAR(20) DEFAULT 'user' NOT NULL"))
                db.session.commit()
                print("[MIGRATION] ✓ user_role column added")
                manish_user = User.query.filter_by(username='manishslal').first()
                if manish_user:
                    manish_user.user_role = 'admin'
                    db.session.commit()
                    print(f"[MIGRATION] ✓ Set {manish_user.username} as admin")
                print("[MIGRATION] ✓ Migration completed")
            else:
                print("[MIGRATION] ✓ user_role column already exists")
        except Exception as e:
            print(f"[MIGRATION] Migration check failed: {e}")
            try:
                db.session.rollback()
            except Exception:
                pass

def has_complete_final_data(bet_data: dict) -> bool:
    legs = bet_data.get('legs', [])
    if not legs:
        return False
    for leg in legs:
        has_final = leg.get('final_value') is not None or leg.get('current') is not None
        if not has_final:
            return False
    return True

from typing import List, Any
from models import db, BetLeg
import logging

def save_final_results_to_bet(bet: Any, processed_data: List[dict]) -> bool:
    try:
        bet_data = bet.get_bet_data()
        matching_parlay = None
        for p in processed_data:
            if p.get('bet_id') == bet_data.get('bet_id') or p.get('name') == bet_data.get('name'):
                matching_parlay = p
                break
        if not matching_parlay:
            return False
        bet_legs = db.session.query(BetLeg).filter(BetLeg.bet_id == bet.id).order_by(BetLeg.leg_order).all()
        updated = False
        for i, leg in enumerate(bet_data.get('legs', [])):
            if i < len(matching_parlay.get('legs', [])):
                processed_leg = matching_parlay['legs'][i]
                if processed_leg.get('gameStatus') == 'STATUS_FINAL':
                    if 'score' not in leg:
                        leg['score'] = processed_leg.get('score', {})
                        updated = True
                    if 'final_value' not in leg and 'current' in processed_leg:
                        leg['final_value'] = processed_leg['current']
                        updated = True
                    if 'result' not in leg and 'status' in processed_leg:
                        leg['result'] = processed_leg['status']
                        updated = True
                    if i < len(bet_legs):
                        bet_leg = bet_legs[i]
                        if processed_leg.get('current') is not None and bet_leg.achieved_value is None:
                            bet_leg.achieved_value = processed_leg['current']
                            updated = True
                            logging.info(f"Saved achieved_value={processed_leg['current']} for leg {i}: {bet_leg.player_name or bet_leg.team}")
                        if bet_leg.game_status != 'STATUS_FINAL':
                            bet_leg.game_status = 'STATUS_FINAL'
                            updated = True
                        if processed_leg.get('homeScore') is not None:
                            bet_leg.home_score = processed_leg['homeScore']
                            bet_leg.away_score = processed_leg['awayScore']
                            updated = True
                        if bet_leg.status == 'pending':
                            leg_status = None
                            stat_type = bet_leg.bet_type.lower()
                            
                            if stat_type == 'moneyline':
                                if bet_leg.achieved_value is not None:
                                    leg_status = 'won' if bet_leg.achieved_value > 0 else 'lost'
                            elif stat_type == 'spread':
                                if bet_leg.achieved_value is not None and bet_leg.target_value is not None:
                                    leg_status = 'won' if (bet_leg.achieved_value + bet_leg.target_value) > 0 else 'lost'
                            else:
                                if bet_leg.achieved_value is not None and bet_leg.target_value is not None:
                                    if bet_leg.bet_line_type == 'under':
                                        leg_status = 'won' if bet_leg.achieved_value < bet_leg.target_value else 'lost'
                                    else:
                                        leg_status = 'won' if bet_leg.achieved_value >= bet_leg.target_value else 'lost'
                            
                            if leg_status:
                                bet_leg.status = leg_status
                                bet_leg.is_hit = True if leg_status == 'won' else False
                                updated = True
                                logging.info(f"Set status={leg_status}, is_hit={bet_leg.is_hit} for leg {i}: {bet_leg.player_name or bet_leg.team}")
        if updated:
            bet.set_bet_data(bet_data, preserve_status=True)
            db.session.commit()
            logging.info(f"Saved final results for bet {bet.id}")
            return True
    except Exception as e:
        logging.error(f"Error saving final results: {e}")
        db.session.rollback()
    return False

def auto_move_completed_bets(user_id):
    try:
        from datetime import date, datetime, timedelta
        today = date.today()
        two_days_ago = today - timedelta(days=2)
        
        from app import get_user_bets_from_db, process_parlay_data
        # Include 'won' and 'lost' so we can revert them if games are no longer finished
        bets = get_user_bets_from_db(user_id, status_filter=['pending', 'live', 'won', 'lost'])
        bet_data_list = [bet.to_dict_structured(use_live_data=True) for bet in bets]
        processed_data = process_parlay_data(bet_data_list)
        updated_count = 0
        
        # First pass: Check for bets with all games 2+ days in the past
        for bet in bets[:]:  # Create a copy to avoid modification during iteration
            bet_data = bet.to_dict_structured(use_live_data=False)  # Use stored data, not live
            legs = bet_data.get('legs', [])
            if not legs:
                continue
                
            # Check if all game dates are 2+ days in the past
            all_games_old = True
            for leg in legs:
                game_date_str = leg.get('game_date')
                if game_date_str:
                    try:
                        # Parse the date (assuming format like "2024-10-27")
                        game_date = datetime.strptime(game_date_str, '%Y-%m-%d').date()
                        if game_date >= two_days_ago:
                            all_games_old = False
                            break
                    except (ValueError, TypeError):
                        # If date parsing fails, assume it's not old
                        all_games_old = False
                        break
                else:
                    # If no game date, assume it's not old
                    all_games_old = False
                    break
            
            # If all games are 2+ days old, move to historical
            if all_games_old:
                logging.info(f"Auto-moving old bet {bet.id} to historical (all games 2+ days old)")
                bet.is_active = False
                # Only set to completed if not already won/lost
                if bet.status not in ['won', 'lost']:
                    bet.status = 'completed'
                bet.api_fetched = 'Yes'  # Mark as processed
                updated_count += 1
                # Remove from bets list so it doesn't get processed again
                bets.remove(bet)
        
        # Track bets that were reverted in this pass to prevent yo-yo effect
        reverted_bets = set()
        
        # Second pass: Process remaining bets with live data (existing logic)
        for bet in bets:
            bet_data = bet.to_dict_structured(use_live_data=True)
            legs = bet_data.get('legs', [])
            if not legs:
                continue
            matching_processed = None
            for p in processed_data:
                # CRITICAL FIX: Use db_id for matching (more reliable than bet_id which is often None)
                # Fall back to name matching only if db_id is not available
                if p.get('db_id') == bet_data.get('db_id'):
                    matching_processed = p
                    break
                elif bet_data.get('db_id') is None and p.get('bet_id') == bet_data.get('bet_id') and bet_data.get('bet_id') is not None:
                    matching_processed = p
                    break
            if not matching_processed:
                if bet.status in ['won', 'lost']:
                    logging.warning(f"[DEBUG BET {bet.id}] No matching_processed found but bet status='{bet.status}' - skipping")
                continue
            has_confirmed_loss = False
            all_games_finished = True
            has_any_not_finished = False  # Track if any games are not finished
            games_data = matching_processed.get('games', [])
            processed_any_leg = False  # Track if we actually processed any legs
            
            # Debug logging for bets 163-166
            if bet.id in [163, 164, 165, 166]:
                logging.warning(f"[DEBUG BET {bet.id}] Starting processing: status={bet.status}, legs_count={len(legs)}, games_count={len(games_data)}")
            
            for i, leg in enumerate(legs):
                processed_leg = matching_processed.get('legs', [])[i] if i < len(matching_processed.get('legs', [])) else None
                if not processed_leg:
                    if bet.id in [163, 164, 165, 166]:
                        logging.warning(f"[DEBUG BET {bet.id}] Leg {i}: No processed_leg found (skipping)")
                    continue
                game_data = None
                leg_away = leg.get('away', '')
                leg_home = leg.get('home', '')
                
                if bet.id in [163, 164, 165, 166]:
                    logging.warning(f"[DEBUG BET {bet.id}] Leg {i}: Looking for game {leg_away} vs {leg_home}")
                
                for game in games_data:
                    teams = game.get('teams', {})
                    game_away = teams.get('away', '')
                    game_home = teams.get('home', '')
                    game_away_abbr = teams.get('away_abbr', '')
                    game_home_abbr = teams.get('home_abbr', '')
                    away_match = (leg_away == game_away or leg_away == game_away_abbr or game_away == leg_away or game_away_abbr == leg_away)
                    home_match = (leg_home == game_home or leg_home == game_home_abbr or game_home == leg_home or game_home_abbr == leg_home)
                    if away_match and home_match:
                        game_data = game
                        if bet.id in [163, 164, 165, 166]:
                            logging.warning(f"[DEBUG BET {bet.id}] Leg {i}: Found game match: {game_away} vs {game_home}, status={game.get('statusTypeName')}")
                        break
                
                if not game_data:
                    all_games_finished = False
                    has_any_not_finished = True
                    if bet.id in [163, 164, 165, 166]:
                        logging.warning(f"[DEBUG BET {bet.id}] Leg {i}: NO GAME FOUND for {leg_away} vs {leg_home}")
                    continue
                processed_any_leg = True  # Mark that we found a matching game for this leg
                game_status = game_data.get('statusTypeName', '')
                if game_status != 'STATUS_FINAL':
                    all_games_finished = False
                    has_any_not_finished = True
                    if bet.id in [163, 164, 165, 166]:
                        logging.warning(f"[DEBUG BET {bet.id}] Leg {i}: Game not finished (status={game_status})")
                else:
                    is_spread_or_ml = leg.get('stat') in ['spread', 'moneyline']
                    # SAFEGUARD: Handle None values for current/target to avoid TypeError
                    current = processed_leg.get('current') or 0
                    target = leg.get('target') or 0
                    if is_spread_or_ml:
                        score_diff = leg.get('score_diff') or processed_leg.get('score_diff') or 0
                        if leg.get('stat') == 'moneyline':
                            if score_diff <= 0:
                                has_confirmed_loss = True
                                logging.info(f"Bet {bet.id} - Leg {i+1} MISS (moneyline lost)")
                        elif leg.get('stat') == 'spread':
                            if (score_diff + target) <= 0:
                                has_confirmed_loss = True
                                logging.info(f"Bet {bet.id} - Leg {i+1} MISS (spread not covered)")
                    else:
                        if target > 0:
                            pct = (current / target) * 100
                            stat_add = leg.get('stat_add') or leg.get('over_under')
                            if leg.get('stat') in ['total_points', 'total_points_under', 'total_points_over']:
                                is_under = stat_add == 'under' or leg.get('stat') == 'total_points_under'
                                is_over = stat_add == 'over' or leg.get('stat') == 'total_points_over'
                                if is_under and pct >= 100:
                                    has_confirmed_loss = True
                                    logging.info(f"Bet {bet.id} - Leg {i+1} MISS (total points under)")
                                elif is_over and pct <= 100:
                                    has_confirmed_loss = True
                                    logging.info(f"Bet {bet.id} - Leg {i+1} MISS (total points over)")
            # Only update bet status if we actually processed at least one leg with complete data
            # AND the bet hasn't already been set to a final status
            if processed_any_leg and all_games_finished and bet.status not in ['won', 'lost', 'completed'] and bet.id not in reverted_bets:
                if has_confirmed_loss:
                    bet.status = 'lost'
                    logging.info(f"Auto-moved bet {bet.id} to LOST")
                else:
                    # Only mark as won if we are sure (all legs checked and no losses)
                    # Since we only checked for losses above, and all games are final,
                    # and we didn't find a loss, it implies a win IF we checked all legs.
                    # However, if some legs were skipped or data missing, it's risky.
                    # For now, defaulting to 'completed' is safer than 'won' for ambiguous cases,
                    # but if we trust the loss check, then 'won' is the logical complement.
                    # Given the bug report, we should be conservative.
                    # Let's check if we actually validated all legs.
                    if len(legs) == len(games_data): # Rough check if we had data for all
                         bet.status = 'won'
                         logging.info(f"Auto-moved bet {bet.id} to WON")
                    else:
                         bet.status = 'completed'
                         logging.info(f"Auto-moved bet {bet.id} to COMPLETED (ambiguous data)")
                updated_count += 1
            elif bet.status in ['won', 'lost'] and has_any_not_finished and processed_any_leg:
                # CRITICAL: Bet was previously marked as won/lost but games are no longer finished
                # Revert it back to 'live' since games are ongoing
                if bet.id in [163, 164, 165, 166]:
                    logging.warning(f"[DEBUG BET {bet.id}] REVERTING: processed_any_leg={processed_any_leg}, has_any_not_finished={has_any_not_finished}, all_games_finished={all_games_finished}")
                logging.warning(f"REVERTING BET {bet.id}: Was marked as '{bet.status}' but games are no longer finished (has_any_not_finished={has_any_not_finished})")
                bet.status = 'live'
                reverted_bets.add(bet.id)  # Track that this bet was reverted
                updated_count += 1
            elif bet.id in [163, 164, 165, 166]:
                logging.warning(f"[DEBUG BET {bet.id}] NO ACTION: status={bet.status}, processed_any_leg={processed_any_leg}, has_any_not_finished={has_any_not_finished}, all_games_finished={all_games_finished}")
        if updated_count > 0:
            db.session.commit()
            logging.info(f"Auto-move completed for {updated_count} bets")
    except Exception as e:
        logging.error(f"Error in auto_move_completed_bets: {e}")
        db.session.rollback()

def auto_move_pending_to_live():
    """Automatically move pending bets to appropriate status based on game states.
    
    - If any games are in progress: move to 'live' status
    - If all games are final: move directly to 'completed' status and deactivate
    """
    try:
        import logging
        from datetime import date
        logging.info("[AUTO-MOVE-PENDING] Checking for pending bets that need status updates")
        
        from models import Bet, BetLeg
        
        # Get all pending bets
        pending_bets = Bet.query.filter_by(status='pending', is_active=True).all()
        
        if not pending_bets:
            logging.info("[AUTO-MOVE-PENDING] No pending bets found")
            return
        
        logging.info(f"[AUTO-MOVE-PENDING] Checking {len(pending_bets)} pending bets")
        
        updated_count = 0
        today = date.today()
        
        for bet in pending_bets:
            # Get bet legs from database
            bet_legs = BetLeg.query.filter(BetLeg.bet_id == bet.id).all()
            
            if not bet_legs:
                continue
            
            # Analyze game statuses
            has_live_games = False
            has_final_games = False
            all_games_final = True
            
            for leg in bet_legs:
                if leg.game_status in ['STATUS_IN_PROGRESS', 'STATUS_HALFTIME']:
                    has_live_games = True
                    all_games_final = False
                elif leg.game_status == 'STATUS_FINAL':
                    has_final_games = True
                else:
                    # Game not started or unknown status
                    all_games_final = False
            
            # Determine new status
            if has_live_games:
                # Has games in progress - move to live
                logging.info(f"[AUTO-MOVE-PENDING] Bet {bet.id} has live games - moving to live status")
                bet.status = 'live'
                updated_count += 1
            elif all_games_final and has_final_games:
                # All games are final - move directly to completed
                logging.info(f"[AUTO-MOVE-PENDING] Bet {bet.id} has all games final - moving to completed")
                
                # Determine won/lost status
                all_legs_won = all(leg.status == 'won' for leg in bet_legs)
                any_leg_lost = any(leg.status == 'lost' for leg in bet_legs)
                
                if all_legs_won:
                    bet.status = 'won'
                elif any_leg_lost:
                    bet.status = 'lost'
                else:
                    # If games are final but we don't have won/lost status (e.g. missing data),
                    # mark as completed for manual review instead of defaulting to won/lost
                    bet.status = 'completed'
                    
                bet.is_active = False  # Move to historical
                updated_count += 1
        
        # Commit all changes
        if updated_count > 0:
            db.session.commit()
            logging.info(f"[AUTO-MOVE-PENDING] Updated {updated_count} bets")
        else:
            logging.info("[AUTO-MOVE-PENDING] No bets needed updating")
            
    except Exception as e:
        logging.error(f"[AUTO-MOVE-PENDING] Error: {e}")
        db.session.rollback()


