"""
Database migration to create audit logging tables.

Creates three tables for comprehensive audit trail:
1. audit_log - General audit trail for all entity changes
2. data_validation_log - Tracks validation results and resolutions
3. automation_runs - Monitors automation health and performance
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'create_audit_tables'
down_revision = None  # Update this if you have previous migrations
branch_labels = None
depends_on = None


def upgrade():
    # Create audit_log table
    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        
        # What happened
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        
        # Who/What did it
        sa.Column('actor_type', sa.String(50), nullable=False),  # 'automation', 'user', 'system'
        sa.Column('actor_name', sa.String(100), nullable=False),
        
        # What was affected
        sa.Column('entity_type', sa.String(50), nullable=False),  # 'bet', 'bet_leg', 'user'
        sa.Column('entity_id', sa.Integer(), nullable=True),
        
        # Details
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        
        # Result
        sa.Column('success', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('error_message', sa.Text(), nullable=True),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for audit_log
    op.create_index('idx_audit_timestamp', 'audit_log', ['timestamp'])
    op.create_index('idx_audit_entity', 'audit_log', ['entity_type', 'entity_id'])
    op.create_index('idx_audit_event', 'audit_log', ['event_type'])
    op.create_index('idx_audit_actor', 'audit_log', ['actor_type', 'actor_name'])
    
    # Create data_validation_log table
    op.create_table(
        'data_validation_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('validation_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        
        # What was checked
        sa.Column('bet_id', sa.Integer(), nullable=True),
        sa.Column('bet_leg_id', sa.Integer(), nullable=True),
        sa.Column('player_name', sa.String(100), nullable=True),
        sa.Column('stat_type', sa.String(50), nullable=True),
        
        # Issue details
        sa.Column('issue_type', sa.String(50), nullable=False),  # 'value_mismatch', 'game_id_issue', 'missing_game_id'
        sa.Column('stored_value', sa.Numeric(10, 2), nullable=True),
        sa.Column('espn_value', sa.Numeric(10, 2), nullable=True),
        sa.Column('difference', sa.Numeric(10, 2), nullable=True),
        
        # Game info
        sa.Column('game_id', sa.String(50), nullable=True),
        sa.Column('game_date', sa.Date(), nullable=True),
        sa.Column('teams', sa.String(200), nullable=True),
        
        # Details
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        
        # Resolution
        sa.Column('resolved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', sa.String(100), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for data_validation_log
    op.create_index('idx_validation_unresolved', 'data_validation_log', ['resolved'], 
                    postgresql_where=sa.text('resolved = false'))
    op.create_index('idx_validation_bet', 'data_validation_log', ['bet_id', 'bet_leg_id'])
    op.create_index('idx_validation_run', 'data_validation_log', ['validation_run_id'])
    op.create_index('idx_validation_timestamp', 'data_validation_log', ['timestamp'])
    
    # Create automation_runs table
    op.create_table(
        'automation_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('automation_name', sa.String(100), nullable=False),
        sa.Column('started_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Numeric(10, 2), nullable=True),
        
        # Results
        sa.Column('success_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failure_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('skipped_count', sa.Integer(), nullable=False, server_default='0'),
        
        # Status
        sa.Column('status', sa.String(20), nullable=False),  # 'success', 'partial_failure', 'failed', 'running'
        sa.Column('error_message', sa.Text(), nullable=True),
        
        # Metadata
        sa.Column('processed_items', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for automation_runs
    op.create_index('idx_automation_name', 'automation_runs', ['automation_name'])
    op.create_index('idx_automation_recent', 'automation_runs', [sa.text('started_at DESC')])
    op.create_index('idx_automation_status', 'automation_runs', ['status'])


def downgrade():
    # Drop tables in reverse order
    op.drop_table('automation_runs')
    op.drop_table('data_validation_log')
    op.drop_table('audit_log')
