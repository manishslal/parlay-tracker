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
        bet_legs = bet.bet_legs_rel.order_by(BetLeg.leg_order).all()
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
                            leg_status = 'lost'
                            stat_type = bet_leg.bet_type.lower()
                            if stat_type == 'moneyline':
                                leg_status = 'won' if bet_leg.achieved_value and bet_leg.achieved_value > 0 else 'lost'
                            elif stat_type == 'spread':
                                if bet_leg.achieved_value is not None and bet_leg.target_value is not None:
                                    leg_status = 'won' if (bet_leg.achieved_value + bet_leg.target_value) > 0 else 'lost'
                            else:
                                if bet_leg.achieved_value is not None and bet_leg.target_value is not None:
                                    if bet_leg.bet_line_type == 'under':
                                        leg_status = 'won' if bet_leg.achieved_value < bet_leg.target_value else 'lost'
                                    else:
                                        leg_status = 'won' if bet_leg.achieved_value >= bet_leg.target_value else 'lost'
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
        from datetime import date
        today = date.today()
        from app import get_user_bets_from_db, process_parlay_data
        bets = get_user_bets_from_db(user_id, status_filter=['pending', 'live'])
        bet_data_list = [bet.to_dict_structured(use_live_data=True) for bet in bets]
        processed_data = process_parlay_data(bet_data_list)
        updated_count = 0
        for bet in bets:
            bet_data = bet.to_dict_structured(use_live_data=True)
            legs = bet_data.get('legs', [])
            if not legs:
                continue
            matching_processed = None
            for p in processed_data:
                if p.get('bet_id') == bet_data.get('bet_id') or p.get('name') == bet_data.get('name'):
                    matching_processed = p
                    break
            if not matching_processed:
                continue
            has_confirmed_loss = False
            all_games_finished = True
            games_data = matching_processed.get('games', [])
            for i, leg in enumerate(legs):
                processed_leg = matching_processed.get('legs', [])[i] if i < len(matching_processed.get('legs', [])) else None
                if not processed_leg:
                    continue
                game_data = None
                leg_away = leg.get('away', '')
                leg_home = leg.get('home', '')
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
                        break
                if not game_data:
                    all_games_finished = False
                    continue
                game_status = game_data.get('statusTypeName', '')
                if game_status != 'STATUS_FINAL':
                    all_games_finished = False
                else:
                    is_spread_or_ml = leg.get('stat') in ['spread', 'moneyline']
                    current = processed_leg.get('current', 0)
                    target = leg.get('target', 0)
                    if is_spread_or_ml:
                        score_diff = leg.get('score_diff', processed_leg.get('score_diff', 0))
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
            if has_confirmed_loss and all_games_finished:
                bet.status = 'lost'
                updated_count += 1
                logging.info(f"Auto-moved bet {bet.id} to LOST")
            elif all_games_finished:
                bet.status = 'won'
                updated_count += 1
                logging.info(f"Auto-moved bet {bet.id} to WON")
        if updated_count > 0:
            db.session.commit()
            logging.info(f"Auto-move completed for {updated_count} bets")
    except Exception as e:
        logging.error(f"Error in auto_move_completed_bets: {e}")
        db.session.rollback()
