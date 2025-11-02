#!/usr/bin/env python3
"""
Migration script to add many-to-many relationship between users and bets
This allows multiple users to share/view the same bets
"""
from app import app, db
from models import User, Bet

# Create association table for many-to-many relationship
bet_users = db.Table('bet_users',
    db.Column('bet_id', db.Integer, db.ForeignKey('bets.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('is_primary_bettor', db.Boolean, default=False),  # Track who placed the bet
    db.Column('created_at', db.DateTime, default=db.func.current_timestamp())
)

def create_many_to_many_table():
    """Create the bet_users association table"""
    
    with app.app_context():
        # Check if table already exists
        inspector = db.inspect(db.engine)
        if 'bet_users' in inspector.get_table_names():
            print("✅ Table 'bet_users' already exists")
            return
        
        print("Creating 'bet_users' table...")
        
        # Create the table
        bet_users.create(db.engine, checkfirst=True)
        
        print("✅ Table created successfully")
        
        # Migrate existing bets to use the new relationship
        print("\nMigrating existing bets...")
        all_bets = Bet.query.all()
        
        for bet in all_bets:
            # Add the current owner as the primary bettor
            insert_stmt = bet_users.insert().values(
                bet_id=bet.id,
                user_id=bet.user_id,
                is_primary_bettor=True
            )
            db.engine.execute(insert_stmt)
        
        db.session.commit()
        print(f"✅ Migrated {len(all_bets)} bets to new relationship")

def add_user_to_all_bets(username):
    """Add a user to all existing bets as a viewer"""
    
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
            existing = db.engine.execute(
                bet_users.select().where(
                    db.and_(
                        bet_users.c.bet_id == bet.id,
                        bet_users.c.user_id == user.id
                    )
                )
            ).fetchone()
            
            if not existing:
                # Add user as a viewer (not primary bettor)
                insert_stmt = bet_users.insert().values(
                    bet_id=bet.id,
                    user_id=user.id,
                    is_primary_bettor=False
                )
                db.engine.execute(insert_stmt)
                added_count += 1
        
        db.session.commit()
        print(f"✅ Added '{username}' to {added_count} bets")

def create_new_users():
    """Create the two new users"""
    
    with app.app_context():
        # Create etoteja
        if not User.query.filter_by(username='etoteja').first():
            user1 = User(username='etoteja', email='etoteja@example.com')
            user1.set_password('changeme123')  # Should change this on first login
            db.session.add(user1)
            print("✅ Created user: etoteja")
        else:
            print("ℹ️  User 'etoteja' already exists")
        
        # Create jtahiliani
        if not User.query.filter_by(username='jtahiliani').first():
            user2 = User(username='jtahiliani', email='jtahiliani@example.com')
            user2.set_password('changeme123')  # Should change this on first login
            db.session.add(user2)
            print("✅ Created user: jtahiliani")
        else:
            print("ℹ️  User 'jtahiliani' already exists")
        
        db.session.commit()

if __name__ == '__main__':
    print("="*80)
    print("MANY-TO-MANY RELATIONSHIP SETUP")
    print("="*80)
    
    # Step 1: Create the association table
    print("\n[1/3] Creating association table...")
    create_many_to_many_table()
    
    # Step 2: Create new users
    print("\n[2/3] Creating new users...")
    create_new_users()
    
    # Step 3: Add etoteja to all existing bets
    print("\n[3/3] Adding 'etoteja' to all existing bets...")
    add_user_to_all_bets('etoteja')
    
    print("\n" + "="*80)
    print("✅ SETUP COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("1. Update models.py to use the many-to-many relationship")
    print("2. Update app.py queries to use the new relationship")
    print("3. Users can now share bets!")
