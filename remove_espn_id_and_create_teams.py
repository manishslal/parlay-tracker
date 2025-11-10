#!/usr/bin/env python3
"""
Migration script to:
1. Remove the redundant espn_id column from players table
2. Create a comprehensive teams table for NFL and NBA teams
"""

import psycopg2
import os
import sys

def run_migration():
    """Execute the migration."""
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    try:
        # Connect to database
        print("Connecting to database...")
        conn = psycopg2.connect(database_url, sslmode='require')
        cur = conn.cursor()
        
        # Step 1: Remove espn_id column from players table
        print("\n" + "=" * 80)
        print("STEP 1: Removing espn_id column from players table")
        print("=" * 80)
        
        # Check if column exists
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'players' AND column_name = 'espn_id'
        """)
        
        if cur.fetchone():
            print("Dropping espn_id column...")
            cur.execute("ALTER TABLE players DROP COLUMN espn_id")
            print("✅ Removed espn_id column")
        else:
            print("ℹ️  espn_id column doesn't exist, skipping")
        
        # Step 2: Create teams table
        print("\n" + "=" * 80)
        print("STEP 2: Creating teams table")
        print("=" * 80)
        
        # Check if table already exists
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'teams'
        """)
        
        if cur.fetchone():
            print("⚠️  teams table already exists")
            user_input = input("Do you want to drop and recreate it? (yes/no): ")
            if user_input.lower() == 'yes':
                print("Dropping existing teams table...")
                cur.execute("DROP TABLE teams CASCADE")
                print("✅ Dropped existing teams table")
            else:
                print("Keeping existing teams table")
                conn.commit()
                cur.close()
                conn.close()
                return
        
        print("Creating teams table...")
        cur.execute("""
            CREATE TABLE teams (
                id SERIAL PRIMARY KEY,
                
                -- Basic Team Info
                team_name VARCHAR(100) NOT NULL,
                team_name_short VARCHAR(50),
                team_abbr VARCHAR(10) NOT NULL,
                espn_team_id VARCHAR(50) UNIQUE,
                
                -- Sport & League Info
                sport VARCHAR(50) NOT NULL,
                league VARCHAR(50),
                conference VARCHAR(50),
                division VARCHAR(50),
                
                -- Current Season Record
                games_played INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                ties INTEGER DEFAULT 0,
                win_percentage NUMERIC(5, 3),
                
                -- Standings Info
                division_rank INTEGER,
                conference_rank INTEGER,
                league_rank INTEGER,
                playoff_seed INTEGER,
                games_behind NUMERIC(4, 1),
                streak VARCHAR(20),
                
                -- Team Details
                location VARCHAR(100),
                nickname VARCHAR(50),
                logo_url TEXT,
                color VARCHAR(20),
                alternate_color VARCHAR(20),
                
                -- Status & Metadata
                is_active BOOLEAN DEFAULT TRUE,
                season_year VARCHAR(10),
                last_game_date DATE,
                next_game_date DATE,
                
                -- API References
                api_data_url TEXT,
                last_stats_update TIMESTAMP,
                
                -- Timestamps
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Constraints
                UNIQUE(team_abbr, sport)
            )
        """)
        
        # Create indexes
        print("Creating indexes...")
        cur.execute("CREATE INDEX idx_teams_espn_team_id ON teams(espn_team_id)")
        cur.execute("CREATE INDEX idx_teams_sport ON teams(sport)")
        cur.execute("CREATE INDEX idx_teams_abbr ON teams(team_abbr)")
        cur.execute("CREATE INDEX idx_teams_conference ON teams(conference)")
        cur.execute("CREATE INDEX idx_teams_division ON teams(division)")
        
        conn.commit()
        print("✅ Successfully created teams table with indexes")
        
        # Show table structure
        cur.execute("""
            SELECT column_name, data_type, character_maximum_length, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'teams'
            ORDER BY ordinal_position
        """)
        
        print("\n" + "=" * 80)
        print("Teams table structure:")
        print("=" * 80)
        print(f"{'Column':<25} {'Type':<25} {'Max Length':<12} {'Nullable':<10}")
        print("-" * 80)
        
        for row in cur.fetchall():
            col_name, data_type, max_len, nullable = row
            max_len_str = str(max_len) if max_len else '-'
            print(f"{col_name:<25} {data_type:<25} {max_len_str:<12} {nullable:<10}")
        
        cur.close()
        conn.close()
        
        print("\n✅ Migration completed successfully!")
        
    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration()
