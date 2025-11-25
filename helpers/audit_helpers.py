"""
Audit Logging Helper Functions

Provides simple functions to log events to the audit_log table.
"""

from sqlalchemy import text
from datetime import datetime
import json


def log_audit_event(db_session, event_type, action, actor_type, actor_name, 
                   entity_type, entity_id, old_value=None, new_value=None, 
                   metadata=None, success=True, error_message=None):
    """Log an audit event to the audit_log table.
    
    Args:
        db_session: SQLAlchemy session
        event_type: Type of event (e.g., 'bet_status_change', 'bet_created')
        action: Specific action taken (e.g., 'moved_to_historical', 'created')
        actor_type: Who/what did it ('automation', 'user', 'system')
        actor_name: Name of the actor (e.g., 'auto_move_bets', 'user_123')
        entity_type: What was affected ('bet', 'bet_leg', 'user')
        entity_id: ID of the affected entity
        old_value: Previous value (optional)
        new_value: New value (optional)
        metadata: Additional context as dict (optional)
        success: Whether the action succeeded (default True)
        error_message: Error message if failed (optional)
    """
    try:
        # Convert metadata dict to JSON string if provided
        metadata_json = json.dumps(metadata) if metadata else None
        
        db_session.execute(text("""
            INSERT INTO audit_log 
            (event_type, action, actor_type, actor_name, entity_type, entity_id,
             old_value, new_value, metadata, success, error_message)
            VALUES 
            (:event_type, :action, :actor_type, :actor_name, :entity_type, :entity_id,
             :old_value, :new_value, :metadata::jsonb, :success, :error_message)
        """), {
            'event_type': event_type,
            'action': action,
            'actor_type': actor_type,
            'actor_name': actor_name,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'old_value': old_value,
            'new_value': new_value,
            'metadata': metadata_json,
            'success': success,
            'error_message': error_message
        })
    except Exception as e:
        # Don't fail the main operation if audit logging fails
        import logging
        logging.error(f"[AUDIT-LOG-ERROR] Failed to write audit log: {e}")


def log_bet_created(db_session, bet_id, user_id=None, username='unknown'):
    """Log bet creation."""
    actor_name = f"user_{user_id}" if user_id else username
    log_audit_event(
        db_session=db_session,
        event_type='bet_created',
        action='created',
        actor_type='user',
        actor_name=actor_name,
        entity_type='bet',
        entity_id=bet_id
    )


def log_bet_deleted(db_session, bet_id, user_id=None, username='unknown'):
    """Log bet deletion."""
    actor_name = f"user_{user_id}" if user_id else username
    log_audit_event(
        db_session=db_session,
        event_type='bet_deleted',
        action='deleted',
        actor_type='user',
        actor_name=actor_name,
        entity_type='bet',
        entity_id=bet_id
    )


def log_bet_status_change(db_session, bet_id, old_status, new_status, 
                          old_is_active, new_is_active, automation_name, reason=""):
    """Log bet status change (used by automations)."""
    metadata = {
        'reason': reason,
        'old_is_active': old_is_active,
        'new_is_active': new_is_active
    }
    
    log_audit_event(
        db_session=db_session,
        event_type='bet_status_change',
        action='status_updated',
        actor_type='automation',
        actor_name=automation_name,
        entity_type='bet',
        entity_id=bet_id,
        old_value=old_status,
        new_value=new_status,
        metadata=metadata
    )


def log_leg_value_update(db_session, bet_id, leg_id, player_name, stat_type,
                         old_value, new_value, automation_name):
    """Log bet leg achieved_value update."""
    metadata = {
        'player_name': player_name,
        'stat_type': stat_type
    }
    
    log_audit_event(
        db_session=db_session,
        event_type='leg_value_update',
        action='achieved_value_updated',
        actor_type='automation',
        actor_name=automation_name,
        entity_type='bet_leg',
        entity_id=leg_id,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value),
        metadata=metadata
    )


def log_automation_run(db_session, automation_name, started_at, completed_at,
                       success_count, failure_count, skipped_count, status, 
                       error_message=None, processed_items=None):
    """Log automation run to automation_runs table."""
    try:
        duration = (completed_at - started_at).total_seconds()
        processed_items_json = json.dumps(processed_items) if processed_items else None
        
        db_session.execute(text("""
            INSERT INTO automation_runs
            (automation_name, started_at, completed_at, duration_seconds,
             success_count, failure_count, skipped_count, status, error_message, processed_items)
            VALUES
            (:automation_name, :started_at, :completed_at, :duration_seconds,
             :success_count, :failure_count, :skipped_count, :status, :error_message, :processed_items::jsonb)
        """), {
            'automation_name': automation_name,
            'started_at': started_at,
            'completed_at': completed_at,
            'duration_seconds': duration,
            'success_count': success_count,
            'failure_count': failure_count,
            'skipped_count': skipped_count,
            'status': status,
            'error_message': error_message,
            'processed_items': processed_items_json
        })
    except Exception as e:
        import logging
        logging.error(f"[AUTOMATION-RUN-LOG-ERROR] Failed to log automation run: {e}")
