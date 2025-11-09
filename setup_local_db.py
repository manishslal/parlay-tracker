#!/usr/bin/env python3
"""
Setup Local PostgreSQL Database
Creates the tables and optionally imports data from production
"""

import os
import sys

# Set up local database URL
os.environ['DATABASE_URL'] = 'postgresql://manishslal@localhost/parlays_local'

from app import app, db
from models import User, Bet

def setup_database():
    """Create all tables in the local database"""
    print("=" * 70)
    print("🗄️  SETTING UP LOCAL POSTGRESQL DATABASE")
    print("=" * 70)
    
    with app.app_context():
        print("\n📝 Creating tables...")
        
        # Create all tables
        db.create_all()
        
        print("✅ Tables created successfully!")
        
        # Show what tables exist
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        print(f"\n📋 Created tables: {', '.join(tables)}")
        
        # Check if there are any users
        user_count = User.query.count()
        bet_count = Bet.query.count()
        
        print(f"\n📊 Current data:")
        print(f"   Users: {user_count}")
        print(f"   Bets: {bet_count}")
        
        if user_count == 0:
            print("\n💡 Database is empty. You can:")
            print("   1. Create test users and bets manually")
            print("   2. Import data from production (see import_production_data.py)")
            print("   3. Run migrations on this clean database first")

if __name__ == '__main__':
    setup_database()
