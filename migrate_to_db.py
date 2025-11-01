#!/usr/bin/env python3
"""
migrate_to_db.py - Migrate JSON bet data to SQLite database

This script:
1. Creates the database and tables
2. Creates a default admin user
3. Migrates all bets from JSON files to the database
4. Backs up original JSON files
"""

import os
import json
import sys
from datetime import datetime
from app import app, db
from models import User, Bet

def load_json_file(filename):
    """Load JSON data from file"""
    filepath = os.path.join('data', filename)
    if not os.path.exists(filepath):
        print(f"⚠️  {filename} not found, skipping...")
        return []
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            print(f"✅ Loaded {len(data)} bets from {filename}")
            return data
    except Exception as e:
        print(f"❌ Error loading {filename}: {e}")
        return []

def backup_json_files():
    """Backup existing JSON files"""
    backup_dir = os.path.join('data', 'backup_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    os.makedirs(backup_dir, exist_ok=True)
    
    json_files = ['Todays_Bets.json', 'Live_Bets.json', 'Historical_Bets.json']
    for filename in json_files:
        filepath = os.path.join('data', filename)
        if os.path.exists(filepath):
            backup_path = os.path.join(backup_dir, filename)
            os.rename(filepath, backup_path)
            print(f"📦 Backed up {filename} to {backup_path}")

def create_default_user():
    """Create default admin user"""
    print("\n👤 Creating default admin user...")
    
    username = input("Enter admin username (default: admin): ").strip() or "admin"
    email = input("Enter admin email (default: admin@parlay.local): ").strip() or "admin@parlay.local"
    
    while True:
        password = input("Enter admin password: ").strip()
        if len(password) >= 6:
            break
        print("❌ Password must be at least 6 characters")
    
    # Check if user already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        print(f"⚠️  User '{username}' already exists, skipping...")
        return existing_user
    
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    print(f"✅ Created user: {username} (ID: {user.id})")
    return user

def migrate_bets(user, all_bets):
    """Migrate bets to database"""
    print(f"\n📊 Migrating {len(all_bets)} bets to database...")
    
    migrated = 0
    skipped = 0
    status_counts = {'pending': 0, 'live': 0, 'completed': 0}
    
    for bet_data in all_bets:
        bet_id = bet_data.get('bet_id') or None  # Convert empty string to None
        bet_type = bet_data.get('type') or 'Unknown'
        betting_site = bet_data.get('betting_site') or 'Unknown'
        
        # Determine status from filename (will be set by caller)
        status = bet_data.get('_status', 'pending')
        status_counts[status] = status_counts.get(status, 0) + 1
        
        # For duplicate detection, use a combination of fields
        # Only check if bet_id exists and is not None
        if bet_id:
            existing = Bet.query.filter_by(user_id=user.id, bet_id=bet_id).first()
            if existing:
                skipped += 1
                continue
        
        # Create new bet
        bet = Bet(
            user_id=user.id,
            bet_id=bet_id,
            bet_type=bet_type,
            betting_site=betting_site,
            status=status
        )
        # Preserve the status we just set (don't recalculate from legs)
        bet.set_bet_data(bet_data, preserve_status=True)
        db.session.add(bet)
        migrated += 1
        
        # Commit in batches to avoid memory issues
        if migrated % 50 == 0:
            db.session.commit()
    
    db.session.commit()
    
    print(f"✅ Migrated {migrated} bets")
    print(f"   - Pending: {status_counts.get('pending', 0)}")
    print(f"   - Live: {status_counts.get('live', 0)}")
    print(f"   - Completed: {status_counts.get('completed', 0)}")
    if skipped > 0:
        print(f"⏭️  Skipped {skipped} duplicate bets")

def main():
    print("=" * 60)
    print("🔄 PARLAY TRACKER - DATABASE MIGRATION")
    print("=" * 60)
    
    with app.app_context():
        # Create tables
        print("\n📁 Creating database tables...")
        db.create_all()
        print("✅ Database tables created")
        
        # Load all JSON data
        print("\n📂 Loading JSON bet data...")
        todays_bets = load_json_file('Todays_Bets.json')
        live_bets = load_json_file('Live_Bets.json')
        historical_bets = load_json_file('Historical_Bets.json')
        
        # Add status marker to each bet based on source file
        for bet in todays_bets:
            bet['_status'] = 'pending'
        for bet in live_bets:
            bet['_status'] = 'live'
        for bet in historical_bets:
            bet['_status'] = 'completed'
        
        all_bets = todays_bets + live_bets + historical_bets
        print(f"\n📊 Total bets to migrate: {len(all_bets)}")
        print(f"   - Pending (Todays): {len(todays_bets)}")
        print(f"   - Live: {len(live_bets)}")
        print(f"   - Completed (Historical): {len(historical_bets)}")
        
        if not all_bets:
            print("⚠️  No bets found to migrate")
        
        # Create default user
        user = create_default_user()
        
        # Migrate bets
        if all_bets:
            migrate_bets(user, all_bets)
        
        # Backup JSON files
        print("\n📦 Backing up JSON files...")
        backup_json_files()
        
        # Summary
        print("\n" + "=" * 60)
        print("✅ MIGRATION COMPLETE!")
        print("=" * 60)
        print(f"Users created: 1")
        print(f"Bets migrated: {Bet.query.filter_by(user_id=user.id).count()}")
        print(f"\n🔑 Login credentials:")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Password: (the one you just entered)")
        print("\n💡 You can now login to the app with these credentials!")
        print("=" * 60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
