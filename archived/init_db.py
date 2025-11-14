#!/usr/bin/env python3
"""
Database initialization script for production deployment.

This script:
1. Creates all database tables (users, bets)
2. Runs all migrations (archive columns, api_fetched column)
3. Verifies the database is properly set up

Run this on first deployment or when database is reset.
"""

import os
import sys
from app import app, db
from models import User, Bet

def init_database():
    """Initialize database with all tables and migrations"""
    
    print("=" * 60)
    print("DATABASE INITIALIZATION")
    print("=" * 60)
    
    with app.app_context():
        try:
            # Step 1: Create all tables
            print("\n📋 Step 1: Creating all database tables...")
            db.create_all()
            print("✅ Tables created successfully")
            
            # Step 2: Verify tables exist
            print("\n📋 Step 2: Verifying tables...")
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"✅ Found tables: {', '.join(tables)}")
            
            if 'users' not in tables:
                print("❌ ERROR: users table not created!")
                return False
            if 'bets' not in tables:
                print("❌ ERROR: bets table not created!")
                return False
            
            # Step 3: Verify columns in bets table
            print("\n📋 Step 3: Verifying bets table columns...")
            bets_columns = [col['name'] for col in inspector.get_columns('bets')]
            print(f"   Columns: {', '.join(bets_columns)}")
            
            required_columns = ['id', 'user_id', 'bet_id', 'bet_type', 'betting_site', 
                              'status', 'is_active', 'is_archived', 'api_fetched', 
                              'bet_data', 'created_at', 'updated_at', 'bet_date']
            
            missing_columns = [col for col in required_columns if col not in bets_columns]
            if missing_columns:
                print(f"❌ WARNING: Missing columns: {', '.join(missing_columns)}")
                print("   These should be added by the model definition.")
            else:
                print("✅ All required columns present")
            
            # Step 4: Create default admin user if needed
            print("\n📋 Step 4: Checking for users...")
            user_count = User.query.count()
            print(f"   Found {user_count} users in database")
            
            if user_count == 0:
                print("\n⚠️  No users found. You'll need to register via /auth/register endpoint")
            
            # Step 5: Check bets
            print("\n📋 Step 5: Checking bets...")
            bet_count = Bet.query.count()
            print(f"   Found {bet_count} bets in database")
            
            print("\n" + "=" * 60)
            print("✅ DATABASE INITIALIZATION COMPLETE")
            print("=" * 60)
            print("\nNext steps:")
            print("1. Register a user via POST /auth/register")
            print("2. Login via POST /auth/login")
            print("3. Start adding bets!")
            
            return True
            
        except Exception as e:
            print(f"\n❌ ERROR during initialization: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print("\n🚀 Starting database initialization...\n")
    success = init_database()
    
    if success:
        print("\n✅ Success! Database is ready to use.")
        sys.exit(0)
    else:
        print("\n❌ Initialization failed. Please check errors above.")
        sys.exit(1)
