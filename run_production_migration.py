#!/usr/bin/env python3
"""
Direct Python Migration Runner
Runs migrations using Python only (no psql/pg_dump needed)
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

def get_db_connection():
    """Get database connection"""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set!")
        sys.exit(1)
    
    # Fix Render's postgres:// to postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    return psycopg2.connect(database_url, cursor_factory=RealDictCursor)

def check_migration_status(cursor):
    """Check which migrations have been applied"""
    try:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'schema_migrations'
            )
        """)
        
        if not cursor.fetchone()['exists']:
            return []
        
        cursor.execute("SELECT migration_name FROM schema_migrations ORDER BY applied_at")
        migrations = [row['migration_name'] for row in cursor.fetchall()]
        
        if migrations:
            print(f"📋 Already applied: {', '.join(migrations)}")
        
        return migrations
    except Exception as e:
        print(f"⚠️  Could not check migration status: {e}")
        return []

def run_sql_migration(cursor, sql_file):
    """Run SQL migration file"""
    print(f"\n🔧 Running {sql_file}...")
    
    with open(sql_file, 'r') as f:
        sql = f.read()
    
    try:
        cursor.execute(sql)
        print(f"✅ {sql_file} completed")
        return True
    except Exception as e:
        print(f"❌ Failed to run {sql_file}: {e}")
        return False

def run_data_migration(cursor):
    """Run data migration inline"""
    print("\n🔧 Running data migration...")
    
    # Import the migration module
    sys.path.insert(0, 'migrations')
    from migrations.migrate_bet_data_002 import migrate_all_data
    
    try:
        migrate_all_data(cursor)
        print("✅ Data migration completed")
        return True
    except Exception as e:
        print(f"❌ Data migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 70)
    print("🗄️  PRODUCTION DATABASE MIGRATION")
    print("=" * 70)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("✅ Connected to database")
        
        # Check migration status
        applied = check_migration_status(cursor)
        
        # Confirm
        print("\n" + "=" * 70)
        print("⚠️  WARNING: This will modify your PRODUCTION database")
        print("=" * 70)
        print("\nMigrations to apply:")
        
        if '001_create_new_schema' not in applied:
            print("  1. ✓ Create new schema (tables & columns)")
        else:
            print("  1. ⏭️  Schema already created")
        
        if '002_migrate_bet_data' not in applied:
            print("  2. ✓ Migrate bet data to structured format")
        else:
            print("  2. ⏭️  Data already migrated")
        
        if '001_create_new_schema' in applied and '002_migrate_bet_data' in applied:
            print("\n✅ All migrations already applied!")
            return
        
        response = input("\n❓ Proceed with migration? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("❌ Migration cancelled")
            return
        
        print("\n" + "=" * 70)
        print("🚀 Starting Migration")
        print("=" * 70)
        
        success = True
        
        # Migration 1: Schema
        if '001_create_new_schema' not in applied:
            if not run_sql_migration(cursor, 'migrations/001_create_new_schema.sql'):
                success = False
                conn.rollback()
            else:
                conn.commit()
        
        # Migration 2: Data
        if success and '002_migrate_bet_data' not in applied:
            # Run the migration script directly
            print("\n🔧 Running data migration...")
            import subprocess
            result = subprocess.run(
                [sys.executable, 'migrations/002_migrate_bet_data.py'],
                env={**os.environ, 'DATABASE_URL': os.environ.get('DATABASE_URL')},
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Data migration completed")
                if result.stdout:
                    print(result.stdout)
            else:
                print("❌ Data migration failed")
                if result.stderr:
                    print(result.stderr)
                success = False
        
        if success:
            print("\n" + "=" * 70)
            print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
            print("=" * 70)
            print("\nYour database now has:")
            print("  - Structured players table")
            print("  - Bet legs with detailed tracking")
            print("  - Tax data summaries")
            print("  - Enhanced bets table with 20+ new columns")
        else:
            print("\n" + "=" * 70)
            print("❌ MIGRATION FAILED")
            print("=" * 70)
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()
