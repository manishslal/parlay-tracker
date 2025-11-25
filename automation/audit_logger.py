"""
Audit logging utilities for bet automations.

Provides functions to create audit trail for critical operations.
"""

import logging
from datetime import datetime


def log_bet_status_change(bet_id, old_status, new_status, old_is_active, new_is_active, automation_name, reason=""):
    """Log a bet status change to create audit trail.
    
    Args:
        bet_id: ID of the bet
        old_status: Previous status value
        new_status: New status value
        old_is_active: Previous is_active value
        new_is_active: New is_active value
        automation_name: Name of automation making the change
        reason: Optional reason for the change
    """
    timestamp = datetime.utcnow().isoformat()
    
    # Build change description
    changes = []
    if old_status != new_status:
        changes.append(f"status: '{old_status}' → '{new_status}'")
    if old_is_active != new_is_active:
        active_str = "live" if new_is_active else "historical"
        changes.append(f"moved to {active_str}")
    
    change_desc = ", ".join(changes)
    
    # Log at INFO level for audit trail
    log_msg = f"[AUDIT] Bet {bet_id} | {automation_name} | {change_desc}"
    if reason:
        log_msg += f" | Reason: {reason}"
    log_msg += f" | Time: {timestamp}"
    
    logging.info(log_msg)
    
    # TODO: In future, write to bet_history table for persistent audit trail
    # For now, logs provide basic audit capability


def log_leg_value_change(bet_id, leg_order, player_name, stat_type, old_value, new_value, automation_name):
    """Log a leg achieved_value change to create audit trail.
    
    Args:
        bet_id: ID of the bet
        leg_order: Order of the leg
        player_name: Player name
        stat_type: Stat type
        old_value: Previous achieved_value
        new_value: New achieved_value
        automation_name: Name of automation making the change
    """
    timestamp = datetime.utcnow().isoformat()
    
    log_msg = (f"[AUDIT] Bet {bet_id} Leg {leg_order} | {automation_name} | "
               f"{player_name} {stat_type}: {old_value} → {new_value} | Time: {timestamp}")
    
    logging.info(log_msg)


def log_automation_run(automation_name, success_count, failure_count, duration_seconds):
    """Log automation run summary for monitoring.
    
    Args:
        automation_name: Name of the automation
        success_count: Number of successful updates
        failure_count: Number of failed updates
        duration_seconds: How long the automation took to run
    """
    timestamp = datetime.utcnow().isoformat()
    
    log_msg = (f"[AUDIT-RUN] {automation_name} | "
               f"Success: {success_count}, Failures: {failure_count}, "
               f"Duration: {duration_seconds:.2f}s | Time: {timestamp}")
    
    logging.info(log_msg)
