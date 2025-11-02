#!/usr/bin/env python3
"""
Simple solution: Add bettor tags to bet_data and create shared bet access
This keeps the current single-owner structure but adds bettor tracking
"""
from app import app, db
from models import User, Bet
import json

def create_new_users():
    """Create etoteja and jtahiliani users"""
    
    with app.app_context():
        users_created = []
        
        # Create etoteja
        if not User.query.filter_by(username='etoteja').first():
            user1 = User(username='etoteja', email='etoteja@example.com')
            user1.set_password('changeme123')  # They should change on first login
            db.session.add(user1)
            users_created.append('etoteja')
            print("✅ Created user: etoteja (password: changeme123)")
        else:
            print("ℹ️  User 'etoteja' already exists")
        
        # Create jtahiliani
        if not User.query.filter_by(username='jtahiliani').first():
            user2 = User(username='jtahiliani', email='jtahiliani@example.com')
            user2.set_password('changeme123')  # They should change on first login
            db.session.add(user2)
            users_created.append('jtahiliani')
            print("✅ Created user: jtahiliani (password: changeme123)")
        else:
            print("ℹ️  User 'jtahiliani' already exists")
        
        db.session.commit()
        
        return users_created

def tag_existing_bets_with_bettor():
    """Add 'bettor' field to all existing bets and set to 'manishslal'"""
    
    with app.app_context():
        # Get manishslal user
        manish = User.query.filter_by(username='manishslal').first()
        
        if not manish:
            print("❌ User 'manishslal' not found")
            return
        
        # Get all bets owned by manishslal
        bets = Bet.query.filter_by(user_id=manish.id).all()
        
        print(f"\nTagging {len(bets)} bets with bettor='manishslal'...")
        
        updated_count = 0
        for bet in bets:
            bet_data = bet.get_bet_data()
            
            # Add bettor field if not present
            if 'bettor' not in bet_data:
                bet_data['bettor'] = 'manishslal'
                bet.set_bet_data(bet_data, preserve_status=True)
                updated_count += 1
        
        db.session.commit()
        print(f"✅ Tagged {updated_count} bets with bettor='manishslal'")

def copy_bets_to_user(username):
    """Copy all manishslal's bets to another user so they can view them"""
    
    with app.app_context():
        # Get users
        manish = User.query.filter_by(username='manishslal').first()
        target_user = User.query.filter_by(username=username).first()
        
        if not manish or not target_user:
            print(f"❌ User not found")
            return
        
        # Get all bets from manishslal
        source_bets = Bet.query.filter_by(user_id=manish.id).all()
        
        print(f"\nCopying {len(source_bets)} bets to '{username}'...")
        
        copied_count = 0
        for source_bet in source_bets:
            # Check if bet already exists for target user (by bet_id)
            bet_data = source_bet.get_bet_data()
            bet_id = bet_data.get('bet_id')
            
            if bet_id:
                existing = Bet.query.filter_by(
                    user_id=target_user.id,
                    bet_id=bet_id
                ).first()
                
                if existing:
                    continue  # Skip if already exists
            
            # Create a copy of the bet for the target user
            new_bet = Bet(user_id=target_user.id)
            new_bet.set_bet_data(bet_data, preserve_status=True)
            new_bet.status = source_bet.status
            new_bet.is_active = source_bet.is_active
            new_bet.is_archived = source_bet.is_archived
            new_bet.api_fetched = source_bet.api_fetched
            
            db.session.add(new_bet)
            copied_count += 1
        
        db.session.commit()
        print(f"✅ Copied {copied_count} bets to '{username}'")

if __name__ == '__main__':
    print("="*80)
    print("SHARED BETS SETUP (Simple Copy Approach)")
    print("="*80)
    
    # Step 1: Create new users
    print("\n[Step 1] Creating new users...")
    new_users = create_new_users()
    
    # Step 2: Tag existing bets with bettor
    print("\n[Step 2] Tagging existing bets...")
    tag_existing_bets_with_bettor()
    
    # Step 3: Copy bets to etoteja
    print("\n[Step 3] Copying bets to 'etoteja'...")
    copy_bets_to_user('etoteja')
    
    print("\n" + "="*80)
    print("✅ SETUP COMPLETE")
    print("="*80)
    print("\nSummary:")
    print("- Created users: etoteja, jtahiliani")
    print("- Tagged all existing bets with bettor='manishslal'")
    print("- Copied all bets to 'etoteja' so they can view them")
    print("\nLogin credentials:")
    print("  Username: etoteja / Password: changeme123")
    print("  Username: jtahiliani / Password: changeme123")
    print("\nNote: Users should change passwords on first login")
