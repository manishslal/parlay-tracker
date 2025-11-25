"""
Validation Module for Bet Automations

Provides validation functions to prevent bad data from being written to database.
"""

import logging

# Validation ranges for common stats (min, max, allow_negative)
STAT_VALIDATION_RANGES = {
    # NFL Stats
    'passing_yards': (0, 600, False),
    'rushing_yards': (0, 400, False),
    'receiving_yards': (0, 400, False),
    'receptions': (0, 30, False),
    'passing_touchdowns': (0, 10, False),
    'rushing_touchdowns': (0, 6, False),
    'interceptions_thrown': (0, 10, False),
    'sacks': (0, 10, False),
    'tackles_assists': (0, 30, False),
    
    # NBA Stats
    'points': (0, 100, False),
    'rebounds': (0, 40, False),
    'assists': (0, 30, False),
    'steals': (0, 15, False),
    'blocks': (0, 15, False),
    'turnovers': (0, 20, False),
    'three_pointers_made': (0, 20, False),
    'made_threes': (0, 20, False),
    '3_pointers_made': (0, 20, False),
    
    # Team Props
    'moneyline': (-100, 100, True),  # Score differential
    'spread': (-100, 100, True),  # Score differential
    'point_spread': (-100, 100, True),  # Score differential
    'total_points': (0, 200, False),
}


def validate_achieved_value(stat_type, value, player_name=None):
    """Validate that an achieved value is reasonable for the stat type.
    
    Args:
        stat_type: The type of stat (e.g., 'points', 'rebounds')
        value: The achieved value to validate
        player_name: Optional player name for logging
        
    Returns:
        tuple: (is_valid, reason)
            is_valid: True if value passes validation
            reason: String explanation if invalid, None if valid
    """
    # None is always invalid for achieved_value
    if value is None:
        return (False, "Value is None")
    
    # Check if stat type has defined range
    stat_type_lower = stat_type.lower() if stat_type else ''
    
    if stat_type_lower not in STAT_VALIDATION_RANGES:
        # Unknown stat type - accept any reasonable value (0 to 1000)
        if value < 0 or value > 1000:
            return (False, f"Value {value} outside reasonable range [0, 1000] for unknown stat '{stat_type}'")
        return (True, None)
    
    min_val, max_val, allow_negative = STAT_VALIDATION_RANGES[stat_type_lower]
    
    # Check if negative values are allowed
    if value < 0 and not allow_negative:
        return (False, f"Negative value {value} not allowed for stat '{stat_type}'")
    
    # Check range
    if value < min_val or value > max_val:
        return (False, f"Value {value} outside valid range [{min_val}, {max_val}] for stat '{stat_type}'")
    
    return (True, None)


def validate_game_status_transition(old_status, new_status):
    """Validate that a game status transition is valid.
    
    Valid transitions:
    - None/unknown -> any
    - STATUS_SCHEDULED -> STATUS_IN_PROGRESS, STATUS_FINAL
    - STATUS_IN_PROGRESS -> STATUS_HALFTIME, STATUS_END_PERIOD, STATUS_FINAL
    - STATUS_HALFTIME -> STATUS_IN_PROGRESS, STATUS_FINAL
    - STATUS_END_PERIOD -> STATUS_IN_PROGRESS, STATUS_FINAL
    - STATUS_FINAL -> (no transitions allowed)
    
    Args:
        old_status: Current game status
        new_status: Proposed new game status
        
    Returns:
        tuple: (is_valid, reason)
    """
    # If old status is None/unknown, allow any transition
    if not old_status or old_status in ['unknown', 'Unknown']:
        return (True, None)
    
    # If new status is same as old, that's always valid
    if old_status == new_status:
        return (True, None)
    
    # Define valid transitions
    valid_transitions = {
        'STATUS_SCHEDULED': ['STATUS_IN_PROGRESS', 'STATUS_FINAL', 'STATUS_HALFTIME'],
        'STATUS_IN_PROGRESS': ['STATUS_HALFTIME', 'STATUS_END_PERIOD', 'STATUS_FINAL'],
        'STATUS_HALFTIME': ['STATUS_IN_PROGRESS', 'STATUS_FINAL', 'STATUS_END_PERIOD'],
        'STATUS_END_PERIOD': ['STATUS_IN_PROGRESS', 'STATUS_FINAL', 'STATUS_HALFTIME'],
        'STATUS_FINAL': [],  # No transitions from final
    }
    
    # Check if transition is valid
    allowed_next = valid_transitions.get(old_status, [])
    if new_status not in allowed_next:
        return (False, f"Invalid transition from '{old_status}' to '{new_status}'")
    
    return (True, None)


def validate_bet_movement(bet, reason=""):
    """Validate that a bet is ready to be moved to historical.
    
    Checks:
    - All legs have STATUS_FINAL
    - At least one leg has achieved_value
    - Bet has valid status
    
    Args:
        bet: Bet object
        reason: Optional reason for movement (for logging)
        
    Returns:
        tuple: (is_valid, reason)
    """
    # Check bet has legs
    if not hasattr(bet, 'bet_legs_rel') or not bet.bet_legs_rel:
        return (False, "Bet has no legs")
    
    # Check all legs are final
    non_final_legs = []
    legs_without_data = []
    
    for leg in bet.bet_legs_rel:
        if leg.game_status != 'STATUS_FINAL':
            non_final_legs.append(f"Leg {leg.leg_order}: {leg.game_status}")
        
        if leg.achieved_value is None:
            legs_without_data.append(f"Leg {leg.leg_order}")
    
    if non_final_legs:
        return (False, f"Not all legs final: {', '.join(non_final_legs)}")
    
    if legs_without_data:
        return (False, f"Legs without data: {', '.join(legs_without_data)}")
    
    return (True, None)


def log_validation_failure(log_prefix, validation_failure_reason, **context):
    """Helper to log validation failures with context.
    
    Args:
        log_prefix: Prefix for log message (e.g., '[LIVE-UPDATE]')
        validation_failure_reason: Reason from validation function
        **context: Additional context to log (bet_id, leg_id, etc.)
    """
    context_str = ', '.join(f"{k}={v}" for k, v in context.items())
    logging.warning(f"{log_prefix} Validation failed: {validation_failure_reason} | Context: {context_str}")
