"""
Automation package for Parlay Tracker background jobs.

This package contains all automated background tasks that run periodically
to maintain and update bet data.
"""

# Lazy imports to avoid circular import issues
def __getattr__(name):
    if name == 'update_live_bet_legs':
        from .live_bet_updates import update_live_bet_legs
        return update_live_bet_legs
    elif name == 'update_completed_bet_legs':
        from .completed_bet_updates import update_completed_bet_legs
        return update_completed_bet_legs
    elif name == 'standardize_bet_leg_team_names':
        from .team_name_standardization import standardize_bet_leg_team_names
        return standardize_bet_leg_team_names
    elif name == 'auto_move_bets_no_live_legs':
        from .bet_status_management import auto_move_bets_no_live_legs
        return auto_move_bets_no_live_legs
    elif name == 'auto_determine_leg_hit_status':
        from .bet_status_management import auto_determine_leg_hit_status
        return auto_determine_leg_hit_status
    elif name == 'process_historical_bets_api':
        from .historical_bet_processing import process_historical_bets_api
        return process_historical_bets_api
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")