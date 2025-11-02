#!/usr/bin/env python3
"""
Migration script to set up many-to-many relationship and create new users
This should be run ONCE after deploying the updated models.py
"""
from app import app, db
from models import User, Bet, bet_users
from sqlalchemy import text

def create_bet_users_table():
    """Create the bet_users association table"""
    
    with app.app_context():
        # Check if table already exists
        result = db.session.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'bet_users')"
        )).scalar()
        
        if result:
            print("✅ Table 'bet_users' already exists")
            return True
        
        print("Creating 'bet_users' table...")
        
        # Create the table using SQLAlchemy
        bet_users.create(db.engine, checkfirst=True)
        
        print("✅ Table 'bet_users' created successfully")
        return False  # Table was just created

def migrate_existing_bets():
    """Migrate all existing bets to use the new many-to-many relationship"""
    
    with app.app_context():
        print("\nMigrating existing bets...")
        
        all_bets = Bet.query.all()
        migrated_count = 0
        
        for bet in all_bets:
            # Check if bet already has entries in bet_users
            existing = db.session.execute(
                bet_users.select().where(bet_users.c.bet_id == bet.id)
            ).fetchone()
            
            if not existing:
                # Add the current owner as the primary bettor
                stmt = bet_users.insert().values(
                    bet_id=bet.id,
                    user_id=bet.user_id,
                    is_primary_bettor=True
                )
                db.session.execute(stmt)
                migrated_count += 1
        
        db.session.commit()
        print(f"✅ Migrated {migrated_count} bets to new relationship")

def create_new_users():
    """Create etoteja and jtahiliani users"""
    
    with app.app_context():
        users_created = []
        
        # Create etoteja
        if not User.query.filter_by(username='etoteja').first():
            user1 = User(username='etoteja', email='etoteja@example.com')
            user1.set_password('changeme123')
            db.session.add(user1)
            users_created.append('etoteja')
            print("✅ Created user: etoteja")
        else:
            print("ℹ️  User 'etoteja' already exists")
        
        # Create jtahiliani
        if not User.query.filter_by(username='jtahiliani').first():
            user2 = User(username='jtahiliani', email='jtahiliani@example.com')
            user2.set_password('changeme123')
            db.session.add(user2)
            users_created.append('jtahiliani')
            print("✅ Created user: jtahiliani")
        else:
            print("ℹ️  User 'jtahiliani' already exists")
        
        db.session.commit()
        return users_created

def share_all_bets_with_user(username):
    """Add a user to all existing bets (as a viewer, not primary bettor)"""
    
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        
        if not user:
            print(f"❌ User '{username}' not found")
            return
        
        # Get all bets
        all_bets = Bet.query.all()
        added_count = 0
        
        for bet in all_bets:
            # Check if user already has access
            existing = db.session.execute(
                bet_users.select().where(
                    db.and_(
                        bet_users.c.bet_id == bet.id,
                        bet_users.c.user_id == user.id
                    )
                )
            ).fetchone()
            
            if not existing:
                # Add user as a viewer (not primary bettor)
                stmt = bet_users.insert().values(
                    bet_id=bet.id,
                    user_id=user.id,
                    is_primary_bettor=False
                )
                db.session.execute(stmt)
                added_count += 1
        
        db.session.commit()
        print(f"✅ Shared {added_count} bets with '{username}'")

def verify_migration():
    """Verify the migration was successful"""
    
    with app.app_context():
        print("\n" + "="*80)
        print("VERIFICATION")
        print("="*80)
        
        # Count total bets
        total_bets = Bet.query.count()
        print(f"\nTotal bets in database: {total_bets}")
        
        # Count bet_users entries
        result = db.session.execute(text("SELECT COUNT(*) FROM bet_users")).scalar()
        print(f"Total bet_users entries: {result}")
        
        # Show bets per user
        users = User.query.all()
        for user in users:
            # Count via bet_users table
            count = db.session.execute(
                text("SELECT COUNT(*) FROM bet_users WHERE user_id = :user_id"),
                {"user_id": user.id}
            ).scalar()
            print(f"\n{user.username}:")
            print(f"  - Can view {count} bets")
            
            # Count primary bets
            primary_count = db.session.execute(
                text("SELECT COUNT(*) FROM bet_users WHERE user_id = :user_id AND is_primary_bettor = true"),
                {"user_id": user.id}
            ).scalar()
            print(f"  - Primary bettor on {primary_count} bets")

if __name__ == '__main__':
    print("="*80)
    print("MANY-TO-MANY RELATIONSHIP MIGRATION")
    print("="*80)
    
    try:
        # Step 1: Create the association table
        print("\n[Step 1/5] Creating bet_users table...")
        table_existed = create_bet_users_table()
        
        # Step 2: Migrate existing bets
        if not table_existed:
            print("\n[Step 2/5] Migrating existing bets...")
            migrate_existing_bets()
        else:
            print("\n[Step 2/5] Skipping migration (already done)")
        
        # Step 3: Create new users
        print("\n[Step 3/5] Creating new users...")
        new_users = create_new_users()
        
        # Step 4: Share bets with etoteja
        print("\n[Step 4/5] Sharing all bets with 'etoteja'...")
        share_all_bets_with_user('etoteja')
        
        # Step 5: Verify
        print("\n[Step 5/5] Verifying migration...")
        verify_migration()
        
        print("\n" + "="*80)
        print("✅ MIGRATION COMPLETE")
        print("="*80)
        print("\nLogin credentials for new users:")
        print("  Username: etoteja    | Password: changeme123")
        print("  Username: jtahiliani | Password: changeme123")
        print("\nNote: Users should change passwords on first login")
        print("\nNext steps:")
        print("1. Update app.py to use user.get_all_bets() instead of user.bets")
        print("2. Test login with all three users")
        print("3. Verify bet sharing is working correctly")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
