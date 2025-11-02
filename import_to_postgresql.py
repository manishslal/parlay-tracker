#!/usr/bin/env python3
"""
Import JSON data to PostgreSQL database
Run this on production or with DATABASE_URL set to PostgreSQL
"""
import json
import sys
import os
from datetime import datetime
from app import app, db
from models import User, Bet
from werkzeug.security import generate_password_hash

def import_data(json_file):
    """Import users and bets from JSON to PostgreSQL"""
    
    # Verify we're using PostgreSQL
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if 'postgresql' not in db_uri:
        print(f"❌ ERROR: Not connected to PostgreSQL!")
        print(f"Current DB: {db_uri}")
        print("Set DATABASE_URL environment variable to PostgreSQL connection string.")
        return False
    
    print(f"✅ Connected to PostgreSQL")
    print(f"📁 Reading from: {json_file}")
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    users_data = data['users']
    bets_data = data['bets']
    
    print(f"\n📊 Data to import:")
    print(f"  👥 Users: {len(users_data)}")
    print(f"  🎲 Bets: {len(bets_data)}")
    
    with app.app_context():
        # Check if data already exists
        existing_users = User.query.count()
        existing_bets = Bet.query.count()
        
        if existing_users > 0 or existing_bets > 0:
            print(f"\n⚠️  WARNING: Database not empty!")
            print(f"  Existing users: {existing_users}")
            print(f"  Existing bets: {existing_bets}")
            response = input("Continue and merge data? (yes/no): ")
            if response.lower() != 'yes':
                print("Aborted.")
                return False
        
        # Import Users
        print("\n👥 Importing users...")
        user_id_map = {}  # Old ID -> New User object
        
        for user_data in users_data:
            # Check if user already exists by username or email
            existing = User.query.filter(
                (User.username == user_data['username']) | 
                (User.email == user_data['email'])
            ).first()
            
            if existing:
                print(f"  ⏭️  User '{user_data['username']}' already exists, skipping")
                user_id_map[user_data['id']] = existing
                continue
            
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                is_active=user_data.get('is_active', True)
            )
            user.password_hash = user_data['password_hash']
            
            if user_data.get('created_at'):
                user.created_at = datetime.fromisoformat(user_data['created_at'])
            
            db.session.add(user)
            db.session.flush()  # Get the new ID
            user_id_map[user_data['id']] = user
            print(f"  ✅ Created user: {user.username}")
        
        db.session.commit()
        print(f"✅ Users imported: {len(user_id_map)}")
        
        # Import Bets
        print("\n🎲 Importing bets...")
        imported_bets = 0
        skipped_bets = 0
        
        for bet_data in bets_data:
            old_user_id = bet_data['user_id']
            
            if old_user_id not in user_id_map:
                print(f"  ⚠️  Skipping bet {bet_data['id']}: user {old_user_id} not found")
                skipped_bets += 1
                continue
            
            new_user = user_id_map[old_user_id]
            
            bet = Bet(
                user_id=new_user.id,
                bet_id=bet_data.get('bet_id'),
                status=bet_data.get('status', 'pending'),
                bet_type=bet_data.get('bet_type'),
                betting_site=bet_data.get('betting_site'),
                is_active=bet_data.get('is_active', True),
                is_archived=bet_data.get('is_archived', False),
                api_fetched=bet_data.get('api_fetched', 'No')
            )
            bet.bet_data = bet_data.get('bet_data')  # Set raw JSON string
            
            if bet_data.get('bet_date'):
                bet.bet_date = datetime.fromisoformat(bet_data['bet_date'])
            if bet_data.get('created_at'):
                bet.created_at = datetime.fromisoformat(bet_data['created_at'])
            if bet_data.get('updated_at'):
                bet.updated_at = datetime.fromisoformat(bet_data['updated_at'])
            
            db.session.add(bet)
            imported_bets += 1
            
            if imported_bets % 10 == 0:
                print(f"  📦 Imported {imported_bets} bets...")
        
        db.session.commit()
        
        print(f"\n✅ Migration complete!")
        print(f"  ✅ Bets imported: {imported_bets}")
        if skipped_bets > 0:
            print(f"  ⏭️  Bets skipped: {skipped_bets}")
        
        # Summary
        print(f"\n📊 Final counts:")
        print(f"  👥 Total users: {User.query.count()}")
        print(f"  🎲 Total bets: {Bet.query.count()}")
        print(f"    - Active: {Bet.query.filter_by(is_active=True).count()}")
        print(f"    - Completed: {Bet.query.filter_by(is_active=False).count()}")
        print(f"    - Archived: {Bet.query.filter_by(is_archived=True).count()}")
        
        return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python import_to_postgresql.py <json_file>")
        print("Example: python import_to_postgresql.py sqlite_export_20250101_120000.json")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    if not os.path.exists(json_file):
        print(f"❌ Error: File not found: {json_file}")
        sys.exit(1)
    
    print("🚀 Starting PostgreSQL import...")
    print(f"📊 Database: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
    
    success = import_data(json_file)
    
    if success:
        print("\n✅ Migration successful!")
        print("🎉 Your data is now in PostgreSQL!")
    else:
        print("\n❌ Migration failed or cancelled")
        sys.exit(1)
