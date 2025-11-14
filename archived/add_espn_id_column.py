#!/usr/bin/env python3
"""
Migration script to add espn_id column to players table.
This will store the ESPN player ID for tracking which players have been matched.
"""

import psycopg2
import os
import sys

def add_espn_id_column():
    """Add espn_id column to players table."""
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    try:
        # Connect to database
        print("Connecting to database...")
        conn = psycopg2.connect(database_url, sslmode='require')
        cur = conn.cursor()
        
        # Check if column already exists
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'players' AND column_name = 'espn_id'
        """)
        
        if cur.fetchone():
            print("✅ Column 'espn_id' already exists in players table")
        else:
            # Add the column
            print("Adding espn_id column to players table...")
            cur.execute("""
                ALTER TABLE players 
                ADD COLUMN espn_id VARCHAR(50)
            """)
            
            # Add an index for faster lookups
            print("Creating index on espn_id...")
            cur.execute("""
                CREATE INDEX idx_players_espn_id ON players(espn_id)
            """)
            
            conn.commit()
            print("✅ Successfully added espn_id column with index")
        
        # Show current table structure
        cur.execute("""
            SELECT column_name, data_type, character_maximum_length, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'players'
            ORDER BY ordinal_position
        """)
        
        print("\n" + "=" * 80)
        print("Current players table structure:")
        print("=" * 80)
        print(f"{'Column':<20} {'Type':<20} {'Max Length':<12} {'Nullable':<10}")
        print("-" * 80)
        
        for row in cur.fetchall():
            col_name, data_type, max_len, nullable = row
            max_len_str = str(max_len) if max_len else '-'
            print(f"{col_name:<20} {data_type:<20} {max_len_str:<12} {nullable:<10}")
        
        # Show count of players with/without espn_id
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(espn_id) as with_espn_id,
                COUNT(*) - COUNT(espn_id) as without_espn_id
            FROM players
        """)
        
        total, with_id, without_id = cur.fetchone()
        print("\n" + "=" * 80)
        print("Player ESPN ID status:")
        print("=" * 80)
        print(f"Total players: {total}")
        print(f"With ESPN ID: {with_id}")
        print(f"Without ESPN ID: {without_id}")
        print("=" * 80)
        
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
    add_espn_id_column()
