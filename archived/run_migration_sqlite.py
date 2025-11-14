#!/usr/bin/env python3
"""
SQLite Migration Runner for Local Testing
Simplified version that works with SQLite database
"""

import os
import sys
import sqlite3
import shutil
from datetime import datetime

def backup_database():
    """Create a backup of the SQLite database"""
    db_path = 'instance/parlays.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return None
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"instance/parlays_backup_{timestamp}.db"
    
    try:
        shutil.copy2(db_path, backup_file)
        print(f"✅ Backup created: {backup_file}")
        return backup_file
    except Exception as e:
        print(f"⚠️  Backup failed: {e}")
        return None

def run_sql_migration(db_path, sql_file):
    """Run a SQL migration file on SQLite"""
    try:
        with open(sql_file, 'r') as f:
            sql = f.read()
        
        # SQLite doesn't support some PostgreSQL syntax
        # Remove PostgreSQL-specific commands
        sql = sql.replace('IF NOT EXISTS', 'IF NOT EXISTS')  # This is fine
        sql = sql.replace('ON DELETE CASCADE', 'ON DELETE CASCADE')  # This is fine
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Split by semicolon and execute each statement
        statements = [s.strip() for s in sql.split(';') if s.strip()]
        
        for statement in statements:
            # Skip PostgreSQL-specific syntax
            if 'SELECT EXISTS' in statement:
                continue
            if 'information_schema' in statement:
                continue
                
            try:
                cursor.execute(statement)
            except sqlite3.OperationalError as e:
                # Skip errors for already existing items
                if 'already exists' in str(e) or 'duplicate column' in str(e):
                    print(f"⏭️  Skipping: {str(e)}")
                    continue
                else:
                    raise
        
        conn.commit()
        conn.close()
        print(f"✅ Executed: {sql_file}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to run {sql_file}: {e}")
        return False

def check_migration_status(db_path):
    """Check which migrations have been applied"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if migrations table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='schema_migrations'
        """)
        
        if not cursor.fetchone():
            print("📋 No migrations have been run yet")
            conn.close()
            return []
        
        # Get applied migrations
        cursor.execute("SELECT migration_name FROM schema_migrations ORDER BY applied_at")
        migrations = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if migrations:
            print(f"📋 Already applied migrations: {', '.join(migrations)}")
        else:
            print("📋 No migrations have been run yet")
        
        return migrations
        
    except Exception as e:
        print(f"⚠️  Could not check migration status: {e}")
        return []

def run_python_migration(db_path):
    """Run the Python data migration script"""
    # Set environment variable for the Python script
    os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
    
    try:
        # Import and run the migration
        sys.path.insert(0, 'migrations')
        
        # Run as subprocess to use correct Python env
        import subprocess
        result = subprocess.run(
            [sys.executable, 'migrations/002_migrate_bet_data.py'],
            capture_output=True,
            text=True,
            env={**os.environ, 'DATABASE_URL': f'sqlite:///{db_path}'}
        )
        
        if result.returncode == 0:
            print(f"✅ Data migration completed")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ Data migration failed")
            if result.stderr:
                print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Failed to run data migration: {e}")
        return False

def main():
    print("=" * 70)
    print("🗄️  SQLITE MIGRATION RUNNER (Local Testing)")
    print("=" * 70)
    
    db_path = 'instance/parlays.db'
    
    # Check database exists
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        print("Make sure you're in the Scrapper directory")
        sys.exit(1)
    
    print(f"✅ Found database: {db_path}")
    
    # Check migration status
    applied_migrations = check_migration_status(db_path)
    
    # Ask for confirmation
    print("\n" + "=" * 70)
    print("⚠️  WARNING: This will modify your database structure")
    print("=" * 70)
    print("\nMigrations to be applied:")
    
    migrations_needed = []
    
    if '001_create_new_schema' not in applied_migrations:
        print("  1. 001_create_new_schema.sql - Add new tables and columns")
        migrations_needed.append('schema')
    else:
        print("  1. ✅ Schema already created")
    
    if '002_migrate_bet_data' not in applied_migrations:
        print("  2. 002_migrate_bet_data.py - Migrate existing data")
        migrations_needed.append('data')
    else:
        print("  2. ✅ Data already migrated")
    
    if not migrations_needed:
        print("\n✅ All migrations already applied!")
        return
    
    response = input("\n❓ Do you want to proceed? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("❌ Migration cancelled")
        sys.exit(0)
    
    # Create backup
    backup_choice = input("\n❓ Create backup before migration? (recommended) (yes/no): ").strip().lower()
    
    if backup_choice in ['yes', 'y']:
        backup_database()
    
    # Run migrations
    print("\n" + "=" * 70)
    print("🚀 Starting Migration Process")
    print("=" * 70)
    
    success = True
    
    # Migration 001: Create schema
    if 'schema' in migrations_needed:
        print("\n📝 Step 1: Creating new schema...")
        if not run_sql_migration(db_path, 'migrations/001_create_new_schema.sql'):
            success = False
            print("\n❌ Schema creation failed!")
    
    # Migration 002: Migrate data
    if success and 'data' in migrations_needed:
        print("\n📝 Step 2: Migrating existing data...")
        if not run_python_migration(db_path):
            success = False
            print("\n❌ Data migration failed!")
    
    # Final result
    print("\n" + "=" * 70)
    if success:
        print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Check the database to verify data migrated correctly")
        print("2. Test queries on the new structure")
        print("3. Once confirmed working, run on production (Render)")
    else:
        print("❌ MIGRATION FAILED!")
        print("=" * 70)
        print("\nTo restore from backup:")
        print("1. Find the backup file in instance/parlays_backup_*.db")
        print("2. Copy it back: cp instance/parlays_backup_*.db instance/parlays.db")

if __name__ == '__main__':
    main()
