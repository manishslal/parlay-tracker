"""
Data Validation Automation

Daily check to validate backend data against ESPN API.
Reports discrepancies for manual review.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def validate_historical_bet_data():
    """Daily validation of historical bet data against ESPN API.
    
    Checks:
    1. achieved_value matches ESPN API data
    2. game_id is correctly linked (matches teams/date)
    3. Identifies legs without game_id
    
    Generates report of all discrepancies for manual review.
    """
    from app import app, db
    from models import BetLeg
    from services.bet_service import fetch_game_details_from_espn, calculate_bet_value
    import logging
    
    with app.app_context():
        try:
            logging.info("[DATA-VALIDATION] Starting daily data validation check")
            
            # Get all historical bet legs (completed games)
            historical_legs = BetLeg.query.filter(
                BetLeg.game_status == 'STATUS_FINAL'
            ).all()
            
            if not historical_legs:
                logging.info("[DATA-VALIDATION] No historical bet legs to validate")
                return
            
            logging.info(f"[DATA-VALIDATION] Validating {len(historical_legs)} historical bet legs")
            
            # Tracking for report
            mismatches = []
            game_id_issues = []
            missing_game_ids = []
            validation_errors = []
            
            for leg in historical_legs:
                try:
                    # Skip if no achieved_value (nothing to validate)
                    if leg.achieved_value is None:
                        continue
                    
                    # Check if leg has game_id
                    if not leg.game_id:
                        # Try to find game
                        game_data = fetch_game_details_from_espn(
                            game_date=str(leg.game_date),
                            away_team=leg.away_team,
                            home_team=leg.home_team,
                            sport=leg.sport or 'NBA'
                        )
                        
                        if game_data:
                            missing_game_ids.append({
                                'bet_id': leg.bet_id,
                                'leg_id': leg.id,
                                'player_name': leg.player_name,
                                'stat_type': leg.stat_type,
                                'teams': f"{leg.away_team} @ {leg.home_team}",
                                'game_date': str(leg.game_date),
                                'found_espn_game_id': game_data.get('espn_game_id'),
                                'message': 'Game found on ESPN but not linked'
                            })
                        else:
                            missing_game_ids.append({
                                'bet_id': leg.bet_id,
                                'leg_id': leg.id,
                                'player_name': leg.player_name,
                                'stat_type': leg.stat_type,
                                'teams': f"{leg.away_team} @ {leg.home_team}",
                                'game_date': str(leg.game_date),
                                'found_espn_game_id': None,
                                'message': 'No matching game found on ESPN'
                            })
                        continue
                    
                    # Fetch game data using game_id
                    game_data = fetch_game_details_from_espn(
                        game_date=str(leg.game_date),
                        away_team=leg.away_team,
                        home_team=leg.home_team,
                        sport=leg.sport or 'NBA'
                    )
                    
                    if not game_data:
                        game_id_issues.append({
                            'bet_id': leg.bet_id,
                            'leg_id': leg.id,
                            'player_name': leg.player_name,
                            'game_id': leg.game_id,
                            'teams': f"{leg.away_team} @ {leg.home_team}",
                            'game_date': str(leg.game_date),
                            'issue': 'Game not found on ESPN with stored game_id'
                        })
                        continue
                    
                    # Check if game_id matches
                    espn_game_id = str(game_data.get('espn_game_id', ''))
                    if espn_game_id != leg.game_id:
                        game_id_issues.append({
                            'bet_id': leg.bet_id,
                            'leg_id': leg.id,
                            'player_name': leg.player_name,
                            'stored_game_id': leg.game_id,
                            'espn_game_id': espn_game_id,
                            'teams': f"{leg.away_team} @ {leg.home_team}",
                            'issue': 'game_id mismatch'
                        })
                    
                    # Calculate value from ESPN
                    leg_dict = {
                        'player': leg.player_name,
                        'stat': leg.stat_type,
                        'target': float(leg.target_value) if leg.target_value is not None else 0.0,
                    }
                    
                    espn_value = calculate_bet_value(leg_dict, game_data)
                    
                    # Compare with stored achieved_value
                    stored_value = float(leg.achieved_value) if leg.achieved_value is not None else 0.0
                    
                    # Allow small floating point differences
                    if abs(espn_value - stored_value) > 0.01:
                        mismatches.append({
                            'bet_id': leg.bet_id,
                            'leg_id': leg.id,
                            'player_name': leg.player_name,
                            'stat_type': leg.stat_type,
                            'stored_achieved_value': stored_value,
                            'espn_value': espn_value,
                            'difference': espn_value - stored_value,
                            'game_id': leg.game_id,
                            'teams': f"{leg.away_team} @ {leg.home_team}",
                            'game_date': str(leg.game_date)
                        })
                
                except Exception as e:
                    validation_errors.append({
                        'bet_id': leg.bet_id,
                        'leg_id': leg.id,
                        'player_name': leg.player_name,
                        'error': str(e)
                    })
            
            # Generate Report
            logging.info("[DATA-VALIDATION] ===== VALIDATION REPORT =====")
            logging.info(f"[DATA-VALIDATION] Total legs validated: {len(historical_legs)}")
            logging.info(f"[DATA-VALIDATION] Value mismatches: {len(mismatches)}")
            logging.info(f"[DATA-VALIDATION] Game ID issues: {len(game_id_issues)}")
            logging.info(f"[DATA-VALIDATION] Missing game IDs: {len(missing_game_ids)}")
            logging.info(f"[DATA-VALIDATION] Validation errors: {len(validation_errors)}")
            
            # Log detailed mismatches
            if mismatches:
                logging.warning("[DATA-VALIDATION] ===== VALUE MISMATCHES =====")
                for mismatch in mismatches:
                    logging.warning(
                        f"[DATA-VALIDATION] MISMATCH | Bet {mismatch['bet_id']} Leg {mismatch['leg_id']} | "
                        f"{mismatch['player_name']} {mismatch['stat_type']} | "
                        f"DB: {mismatch['stored_achieved_value']} vs ESPN: {mismatch['espn_value']} "
                        f"(diff: {mismatch['difference']:.2f}) | {mismatch['teams']} | {mismatch['game_date']}"
                    )
            
            # Log game_id issues
            if game_id_issues:
                logging.warning("[DATA-VALIDATION] ===== GAME ID ISSUES =====")
                for issue in game_id_issues:
                    logging.warning(
                        f"[DATA-VALIDATION] GAME_ID_ISSUE | Bet {issue['bet_id']} Leg {issue['leg_id']} | "
                        f"{issue['player_name']} | {issue['teams']} | Issue: {issue['issue']}"
                    )
            
            # Log missing game_ids
            if missing_game_ids:
                logging.warning("[DATA-VALIDATION] ===== MISSING GAME IDS =====")
                for missing in missing_game_ids:
                    esp_id = missing['found_espn_game_id'] or 'NOT_FOUND'
                    logging.warning(
                        f"[DATA-VALIDATION] NO_GAME_ID | Bet {missing['bet_id']} Leg {missing['leg_id']} | "
                        f"{missing['player_name']} {missing['stat_type']} | {missing['teams']} | "
                        f"ESPN ID: {esp_id} | {missing['message']}"
                    )
            
            # Log errors
            if validation_errors:
                logging.error("[DATA-VALIDATION] ===== VALIDATION ERRORS =====")
                for error in validation_errors:
                    logging.error(
                        f"[DATA-VALIDATION] ERROR | Bet {error['bet_id']} Leg {error['leg_id']} | "
                        f"{error['player_name']} | Error: {error['error']}"
                    )
            
            logging.info("[DATA-VALIDATION] ===== END VALIDATION REPORT =====")
            
        except Exception as e:
            logging.error(f"[DATA-VALIDATION] Fatal error: {e}")


if __name__ == "__main__":
    validate_historical_bet_data()
