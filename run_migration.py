#!/usr/bin/env python3
"""
Master Migration Runner
Safely runs all database migrations with backup and rollback capability
"""

import os
import sys
import subprocess
from datetime import datetime
import sqlite3
import shutil

def run_command(cmd, description):
    """Run a shell command and return success status"""
    print(f"\n🔧 {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed: {result.stderr}")
        return False
    
    if result.stdout:
        print(result.stdout)
    return True

def get_database_path():
    """Get the SQLite database path"""
    # Check for DATABASE_URL first (PostgreSQL)
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        return database_url, 'postgresql'
    
    # Default to SQLite
    db_path = 'instance/parlays.db'
    if os.path.exists(db_path):
        print(f"ℹ️  Using local SQLite database: {db_path}")
        return db_path, 'sqlite'
    else:
        print(f"❌ ERROR: Database not found at {db_path}")
        print("\nFor PostgreSQL, set DATABASE_URL:")
        print("export DATABASE_URL='postgresql://...'")
        return None, None

def check_database_connection():
    """Verify database is accessible"""
    db_path, db_type = get_database_path()
    
    if not db_path:
        return False
    
    if db_type == 'sqlite':
        try:
            conn = sqlite3.connect(db_path)
            conn.close()
            print("✅ SQLite database connection successful")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    else:
        # PostgreSQL - try to import and connect
        try:
            import psycopg2
            # Fix Render's postgres:// to postgresql://
            if db_path.startswith('postgres://'):
                db_path = db_path.replace('postgres://', 'postgresql://', 1)
            
            conn = psycopg2.connect(db_path)
            conn.close()
            print("✅ PostgreSQL database connection successful")
            return True
        except ImportError:
            print("❌ psycopg2 not installed. Install with: pip install psycopg2-binary")
            return False
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False

def backup_database():
    """Create a backup of the database before migration"""
    print("\n💾 Creating database backup...")
    
    database_url = os.environ.get('DATABASE_URL')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"backup_before_migration_{timestamp}.sql"
    
    cmd = f'pg_dump "{database_url}" > {backup_file}'
    
    if run_command(cmd, f"Backing up to {backup_file}"):
        print(f"✅ Backup saved to: {backup_file}")
        return backup_file
    else:
        print("⚠️  Backup failed, but continuing...")
        return None

def run_sql_migration(sql_file):
    """Run a SQL migration file"""
    database_url = os.environ.get('DATABASE_URL')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    cmd = f'psql "{database_url}" -f {sql_file}'
    return run_command(cmd, f"Running {sql_file}")

def run_python_migration(py_file):
    """Run a Python migration script"""
    # Use sys.executable to use the same Python interpreter
    cmd = f'{sys.executable} {py_file}'
    return run_command(cmd, f"Running {py_file}")

def check_migration_status():
    """Check which migrations have already been applied"""
    database_url = os.environ.get('DATABASE_URL')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check if migrations table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'schema_migrations'
            )
        """)
        
        if not cursor.fetchone()[0]:
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

def main():
    print("=" * 70)
    print("🗄️  DATABASE MIGRATION RUNNER")
    print("=" * 70)
    
    # Step 1: Check database connection
    if not check_database_connection():
        print("\n❌ Cannot proceed without database connection")
        sys.exit(1)
    
    # Step 2: Check current migration status
    applied_migrations = check_migration_status()
    
    # Step 3: Ask for confirmation
    print("\n" + "=" * 70)
    print("⚠️  WARNING: This will modify your database structure")
    print("=" * 70)
    print("\nMigrations to be applied:")
    print("  1. 001_create_new_schema.sql - Add new tables and columns")
    print("  2. 002_migrate_bet_data.py - Migrate existing data to new structure")
    
    if '001_create_new_schema' in applied_migrations:
        print("\n✅ Schema already created (001_create_new_schema)")
    
    if '002_migrate_bet_data' in applied_migrations:
        print("✅ Data already migrated (002_migrate_bet_data)")
    
    if '001_create_new_schema' in applied_migrations and '002_migrate_bet_data' in applied_migrations:
        print("\n✅ All migrations already applied!")
        return
    
    response = input("\n❓ Do you want to proceed? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("❌ Migration cancelled")
        sys.exit(0)
    
    # Step 4: Create backup (optional but recommended)
    backup_choice = input("\n❓ Create backup before migration? (recommended) (yes/no): ").strip().lower()
    backup_file = None
    
    if backup_choice in ['yes', 'y']:
        backup_file = backup_database()
    
    # Step 5: Run migrations
    print("\n" + "=" * 70)
    print("🚀 Starting Migration Process")
    print("=" * 70)
    
    success = True
    
    # Migration 001: Create schema
    if '001_create_new_schema' not in applied_migrations:
        if not run_sql_migration('migrations/001_create_new_schema.sql'):
            success = False
            print("\n❌ Schema creation failed!")
    else:
        print("\n⏭️  Skipping 001_create_new_schema (already applied)")
    
    # Migration 002: Migrate data
    if success and '002_migrate_bet_data' not in applied_migrations:
        if not run_python_migration('migrations/002_migrate_bet_data.py'):
            success = False
            print("\n❌ Data migration failed!")
    else:
        print("\n⏭️  Skipping 002_migrate_bet_data (already applied)")
    
    # Step 6: Report results
    print("\n" + "=" * 70)
    if success:
        print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("\nNext steps:")
        print("  1. Verify data in database")
        print("  2. Update application code to use new schema")
        print("  3. Deploy updated code")
        
        if backup_file:
            print(f"\n💾 Backup file: {backup_file}")
            print("   Keep this file safe for rollback if needed")
    else:
        print("❌ MIGRATION FAILED")
        print("=" * 70)
        if backup_file:
            print(f"\n💾 Restore from backup: {backup_file}")
            print(f'   psql "$DATABASE_URL" < {backup_file}')
        sys.exit(1)

if __name__ == '__main__':
    main()
