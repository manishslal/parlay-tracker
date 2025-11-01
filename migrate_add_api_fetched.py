#!/usr/bin/env python3
"""
Migration script to add api_fetched column to bets table.

This column tracks whether ESPN API has been called for a bet:
- 'Yes' = ESPN data has been fetched and processed
- 'No' = ESPN data not yet fetched (default)

This allows us to optimize historical endpoint by only calling ESPN
for bets that haven't been fetched yet.
"""

import sqlite3
import os
from datetime import datetime

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'parlays.db')

def migrate():
    """Add api_fetched column to bets table"""
    
    print(f"🔄 Starting migration: Add api_fetched column")
    print(f"📂 Database: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: Database not found at {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(bets)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'api_fetched' in columns:
            print("✅ Column 'api_fetched' already exists. No migration needed.")
            return True
        
        print("\n📋 Adding api_fetched column...")
        
        # Add the api_fetched column
        cursor.execute("""
            ALTER TABLE bets 
            ADD COLUMN api_fetched TEXT DEFAULT 'No' NOT NULL
        """)
        
        print("✅ Column added successfully")
        
        # Set api_fetched='Yes' for completed/historical bets (they've been processed)
        print("\n🔄 Setting api_fetched='Yes' for completed bets...")
        cursor.execute("""
            UPDATE bets 
            SET api_fetched = 'Yes' 
            WHERE is_active = 0
        """)
        completed_count = cursor.rowcount
        print(f"✅ Updated {completed_count} completed bets to api_fetched='Yes'")
        
        # Set api_fetched='No' for active bets (will be fetched when they complete)
        print("\n🔄 Setting api_fetched='No' for active bets...")
        cursor.execute("""
            UPDATE bets 
            SET api_fetched = 'No' 
            WHERE is_active = 1
        """)
        active_count = cursor.rowcount
        print(f"✅ Updated {active_count} active bets to api_fetched='No'")
        
        # Commit changes
        conn.commit()
        
        # Verify the migration
        print("\n📊 Verification:")
        cursor.execute("""
            SELECT api_fetched, COUNT(*) 
            FROM bets 
            GROUP BY api_fetched
        """)
        results = cursor.fetchall()
        for api_status, count in results:
            print(f"  - api_fetched='{api_status}': {count} bets")
        
        print("\n✅ Migration completed successfully!")
        return True
        
    except sqlite3.Error as e:
        print(f"\n❌ Error during migration: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("MIGRATION: Add api_fetched column to bets table")
    print("=" * 60)
    
    success = migrate()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ MIGRATION SUCCESSFUL")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ MIGRATION FAILED")
        print("=" * 60)
        exit(1)
