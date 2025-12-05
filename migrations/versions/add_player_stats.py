"""
Add season_stats and last_stats_update columns to players table.

Revision ID: add_player_stats
Revises: create_audit_tables
Create Date: 2025-12-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_player_stats'
down_revision = 'create_audit_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Add season_stats column (JSONB)
    op.add_column('players', sa.Column('season_stats', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    
    # Add last_stats_update column (DateTime)
    op.add_column('players', sa.Column('last_stats_update', sa.DateTime(), nullable=True))


def downgrade():
    # Remove columns
    op.drop_column('players', 'last_stats_update')
    op.drop_column('players', 'season_stats')
