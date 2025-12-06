"""Add performance indexes

Revision ID: add_performance_indexes
Revises: add_player_stats
Create Date: 2025-12-05 19:24:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_performance_indexes'
down_revision = 'add_player_stats'  # Proper chain: create_audit_tables -> add_player_stats -> add_performance_indexes
branch_labels = None
depends_on = None


def upgrade():
    """Add indexes to improve query performance."""
    
    # Indexes for bets table (commonly filtered/sorted)
    op.create_index('idx_bets_status', 'bets', ['status'])
    op.create_index('idx_bets_created_at', 'bets', ['created_at'])
    op.create_index('idx_bets_status_created', 'bets', ['status', 'created_at'])
    
    # Indexes for bet_legs table (most queried table)
    op.create_index('idx_bet_legs_bet_id', 'bet_legs', ['bet_id'])
    op.create_index('idx_bet_legs_game_date', 'bet_legs', ['game_date'])
    op.create_index('idx_bet_legs_game_id', 'bet_legs', ['game_id'])
    op.create_index('idx_bet_legs_status', 'bet_legs', ['status'])
    op.create_index('idx_bet_legs_sport', 'bet_legs', ['sport'])
    op.create_index('idx_bet_legs_game_status', 'bet_legs', ['game_status'])
    op.create_index('idx_bet_legs_player_id', 'bet_legs', ['player_id'])
    
    # Composite indexes for common query patterns
    op.create_index('idx_bet_legs_date_status', 'bet_legs', ['game_date', 'status'])
    op.create_index('idx_bet_legs_sport_date', 'bet_legs', ['sport', 'game_date'])
    op.create_index('idx_bet_legs_bet_status', 'bet_legs', ['bet_id', 'status'])
    
    # Indexes for teams table (lookups by name)
    op.create_index('idx_teams_team_name', 'teams', ['team_name'])
    op.create_index('idx_teams_sport', 'teams', ['sport'])
    
    # Indexes for players table (lookups by name and sport)
    op.create_index('idx_players_name_sport', 'players', ['player_name', 'sport'])
    op.create_index('idx_players_team_id', 'players', ['team_id'])
    
    # Indexes for games table (date-based queries)
    op.create_index('idx_games_game_date', 'games', ['game_date'])
    op.create_index('idx_games_sport_date', 'games', ['sport', 'game_date'])
    op.create_index('idx_games_status', 'games', ['status'])


def downgrade():
    """Remove performance indexes."""
    
    # Drop bets indexes
    op.drop_index('idx_bets_status', table_name='bets')
    op.drop_index('idx_bets_created_at', table_name='bets')
    op.drop_index('idx_bets_status_created', table_name='bets')
    
    # Drop bet_legs indexes
    op.drop_index('idx_bet_legs_bet_id', table_name='bet_legs')
    op.drop_index('idx_bet_legs_game_date', table_name='bet_legs')
    op.drop_index('idx_bet_legs_game_id', table_name='bet_legs')
    op.drop_index('idx_bet_legs_status', table_name='bet_legs')
    op.drop_index('idx_bet_legs_sport', table_name='bet_legs')
    op.drop_index('idx_bet_legs_game_status', table_name='bet_legs')
    op.drop_index('idx_bet_legs_player_id', table_name='bet_legs')
    op.drop_index('idx_bet_legs_date_status', table_name='bet_legs')
    op.drop_index('idx_bet_legs_sport_date', table_name='bet_legs')
    op.drop_index('idx_bet_legs_bet_status', table_name='bet_legs')
    
    # Drop teams indexes
    op.drop_index('idx_teams_team_name', table_name='teams')
    op.drop_index('idx_teams_sport', table_name='teams')
    
    # Drop players indexes
    op.drop_index('idx_players_name_sport', table_name='players')
    op.drop_index('idx_players_team_id', table_name='players')
    
    # Drop games indexes
    op.drop_index('idx_games_game_date', table_name='games')
    op.drop_index('idx_games_sport_date', table_name='games')
    op.drop_index('idx_games_status', table_name='games')
