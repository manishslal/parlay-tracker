#!/usr/bin/env python3
"""
Migration 004: Reorder bet_legs columns and standardize bet_type values
Purpose: Move stat_type column after bet_type, standardize bet_type values
Safe: Only alters table structure and updates data, preserves all existing data
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    """Get database connection from environment"""
    database_url = os.environ.get('DATABASE_URL')

    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set!")
        print("\nTo set it, run:")
        print("export DATABASE_URL='postgresql://...'")
        sys.exit(1)

    # Fix Render's postgres:// to postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    return psycopg2.connect(database_url, cursor_factory=RealDictCursor)

def reorder_bet_legs_columns():
    """Reorder columns in bet_legs table to put stat_type after bet_type"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        print("🔄 Reordering bet_legs columns...")

        # First, increase the size of stat_type column to accommodate longer stat names
        cursor.execute("ALTER TABLE bet_legs ALTER COLUMN stat_type TYPE VARCHAR(50)")

        # PostgreSQL doesn't have a direct way to reorder columns, so we need to:
        # 1. Create a new table with the desired column order
        # 2. Copy data from old table to new table
        # 3. Drop old table
        # 4. Rename new table

        # Create new table with desired column order
        cursor.execute("""
            CREATE TABLE bet_legs_new (
                id INTEGER PRIMARY KEY,
                bet_id INTEGER REFERENCES bets(id),
                player_id INTEGER REFERENCES players(id),

                -- Player/Team Info (Denormalized for performance)
                player_name VARCHAR(100) NOT NULL,
                player_team VARCHAR(50),
                player_position VARCHAR(10),

                -- Game Info
                home_team VARCHAR(50) NOT NULL,
                away_team VARCHAR(50) NOT NULL,
                game_id VARCHAR(50),
                game_date DATE,
                game_time TIME,
                game_status VARCHAR(20),
                sport VARCHAR(50),
                parlay_sport VARCHAR(50),

                -- Bet Details (reordered)
                bet_type VARCHAR(50) NOT NULL,
                stat_type VARCHAR(50),  -- Moved here, increased size
                bet_line_type VARCHAR(20),  -- 'over', 'under', NULL
                target_value NUMERIC(10, 2) NOT NULL,
                achieved_value NUMERIC(10, 2),

                -- Performance Comparison
                player_season_avg NUMERIC(10, 2),
                player_last_5_avg NUMERIC(10, 2),
                vs_opponent_avg NUMERIC(10, 2),
                target_vs_season NUMERIC(10, 2),

                -- Odds Tracking
                original_leg_odds INTEGER,
                boosted_leg_odds INTEGER,
                final_leg_odds INTEGER,

                -- Leg Status
                status VARCHAR(20) DEFAULT 'pending',
                is_hit BOOLEAN,
                void_reason VARCHAR(100),

                -- Live Game Data
                current_quarter VARCHAR(10),
                time_remaining VARCHAR(20),
                home_score INTEGER,
                away_score INTEGER,

                -- Contextual Data
                is_home_game BOOLEAN,
                weather_conditions VARCHAR(100),
                injury_during_game BOOLEAN DEFAULT FALSE,
                dnp_reason VARCHAR(100),

                -- Metadata
                leg_order INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Copy data from old table to new table
        cursor.execute("""
            INSERT INTO bet_legs_new (
                id, bet_id, player_id, player_name, player_team, player_position,
                home_team, away_team, game_id, game_date, game_time, game_status,
                sport, parlay_sport, bet_type, stat_type, bet_line_type,
                target_value, achieved_value, player_season_avg, player_last_5_avg,
                vs_opponent_avg, target_vs_season, original_leg_odds, boosted_leg_odds,
                final_leg_odds, status, is_hit, void_reason, current_quarter,
                time_remaining, home_score, away_score, is_home_game,
                weather_conditions, injury_during_game, dnp_reason, leg_order,
                created_at, updated_at
            )
            SELECT
                id, bet_id, player_id, player_name, player_team, player_position,
                home_team, away_team, game_id, game_date, game_time, game_status,
                sport, parlay_sport, bet_type, stat_type, bet_line_type,
                target_value, achieved_value, player_season_avg, player_last_5_avg,
                vs_opponent_avg, target_vs_season, original_leg_odds, boosted_leg_odds,
                final_leg_odds, status, is_hit, void_reason, current_quarter,
                time_remaining, home_score, away_score, is_home_game,
                weather_conditions, injury_during_game, dnp_reason, leg_order,
                created_at, updated_at
            FROM bet_legs
        """)

        # Drop old table
        cursor.execute("DROP TABLE bet_legs")

        # Rename new table
        cursor.execute("ALTER TABLE bet_legs_new RENAME TO bet_legs")

        # Recreate indexes if they existed
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bet_legs_bet_id ON bet_legs(bet_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bet_legs_player_id ON bet_legs(player_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bet_legs_game_id ON bet_legs(game_id)")

        conn.commit()
        print("✓ Column reordering completed")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error reordering columns: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def standardize_bet_types():
    """Update bet_legs to have proper bet_type values and move stat details to stat_type"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        print("🔄 Standardizing bet_type values...")

        # First, let's see what bet_type values we currently have
        cursor.execute("SELECT DISTINCT bet_type FROM bet_legs ORDER BY bet_type")
        current_types = cursor.fetchall()
        print(f"Current bet_type values: {[row['bet_type'] for row in current_types]}")

        # Define mapping from current bet_type values to standardized ones
        # If bet_type contains specific stat info, move it to stat_type and set bet_type to "Player Prop" or "Team Prop"
        bet_type_mappings = {
            # Player Props - move specific stat to stat_type
            'receiving yards': ('Player Prop', 'receiving yards'),
            'passing yards': ('Player Prop', 'passing yards'),
            'rushing yards': ('Player Prop', 'rushing yards'),
            'passing tds': ('Player Prop', 'passing tds'),
            'rushing tds': ('Player Prop', 'rushing tds'),
            'receiving tds': ('Player Prop', 'receiving tds'),
            'receptions': ('Player Prop', 'receptions'),
            'field goals made': ('Player Prop', 'field goals made'),
            'extra points made': ('Player Prop', 'extra points made'),
            'points': ('Player Prop', 'points'),
            'rebounds': ('Player Prop', 'rebounds'),
            'assists': ('Player Prop', 'assists'),
            'steals': ('Player Prop', 'steals'),
            'blocks': ('Player Prop', 'blocks'),
            'strikeouts': ('Player Prop', 'strikeouts'),
            'hits': ('Player Prop', 'hits'),
            'home runs': ('Player Prop', 'home runs'),
            'total bases': ('Player Prop', 'total bases'),

            # Team Props
            'team total points': ('Team Prop', 'total points'),
            'first team to score': ('Team Prop', 'first team to score'),
            'total points': ('Team Prop', 'total points'),

            # Keep these as-is if they're already standardized
            'Player Prop': ('Player Prop', None),
            'Team Prop': ('Team Prop', None),
        }

        # Update each bet_type
        for old_type, (new_bet_type, stat_type) in bet_type_mappings.items():
            if stat_type:
                # Move specific stat to stat_type column
                cursor.execute("""
                    UPDATE bet_legs
                    SET bet_type = %s, stat_type = %s
                    WHERE bet_type = %s AND (stat_type IS NULL OR stat_type = '')
                """, (new_bet_type, stat_type, old_type))
                print(f"✓ Updated '{old_type}' -> bet_type: '{new_bet_type}', stat_type: '{stat_type}'")
            else:
                # Just update bet_type
                cursor.execute("""
                    UPDATE bet_legs
                    SET bet_type = %s
                    WHERE bet_type = %s
                """, (new_bet_type, old_type))
                print(f"✓ Updated '{old_type}' -> bet_type: '{new_bet_type}'")

        # Handle any remaining bet_types that might not be in our mapping
        cursor.execute("""
            SELECT DISTINCT bet_type FROM bet_legs
            WHERE bet_type NOT IN ('Player Prop', 'Team Prop')
        """)
        remaining = cursor.fetchall()
        if remaining:
            print(f"⚠️  Remaining unmapped bet_types: {[row['bet_type'] for row in remaining]}")
            # For any remaining, assume they're player props and move to stat_type
            for row in remaining:
                old_type = row['bet_type']
                cursor.execute("""
                    UPDATE bet_legs
                    SET bet_type = 'Player Prop', stat_type = %s
                    WHERE bet_type = %s AND (stat_type IS NULL OR stat_type = '')
                """, (old_type, old_type))
                print(f"✓ Auto-mapped '{old_type}' -> bet_type: 'Player Prop', stat_type: '{old_type}'")

        conn.commit()
        print("✓ Bet type standardization completed")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error standardizing bet types: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def main():
    """Run the migration"""
    print("🚀 Starting Migration 004: Reorder bet_legs columns and standardize bet_type values")
    print("=" * 80)

    try:
        reorder_bet_legs_columns()
        standardize_bet_types()

        print("=" * 80)
        print("✅ Migration 004 completed successfully!")
        print("\nNext steps:")
        print("1. Restart your application to ensure it works with the new column order")
        print("2. Test the frontend to verify stat_type is displayed instead of bet_type")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()