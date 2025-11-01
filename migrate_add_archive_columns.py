#!/usr/bin/env python3
"""
Migration script to add is_active and is_archived columns to bets table
"""
from app import app, db
from models import Bet

def migrate_add_archive_columns():
    """Add is_active and is_archived columns to existing bets"""
    with app.app_context():
        print("Starting migration to add is_active and is_archived columns...")
        
        # Add the columns using raw SQL (SQLAlchemy doesn't auto-migrate)
        try:
            # Check if columns already exist
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('bets')]
            
            if 'is_active' not in columns:
                print("Adding is_active column...")
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE bets ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1'))
                    conn.commit()
                print("✅ Added is_active column")
            else:
                print("⚠️  is_active column already exists")
            
            if 'is_archived' not in columns:
                print("Adding is_archived column...")
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE bets ADD COLUMN is_archived BOOLEAN NOT NULL DEFAULT 0'))
                    conn.commit()
                print("✅ Added is_archived column")
            else:
                print("⚠️  is_archived column already exists")
            
            # Update existing bets based on their current status
            print("\nUpdating existing bets...")
            
            # All bets with status='archived' should have is_archived=1
            archived_count = db.session.query(Bet).filter_by(status='archived').update(
                {'is_archived': True},
                synchronize_session=False
            )
            print(f"  Set is_archived=1 for {archived_count} bets with status='archived'")
            
            # All bets with status='completed' should have is_active=0 (unless already archived)
            completed_count = db.session.query(Bet).filter_by(status='completed', is_archived=False).update(
                {'is_active': False},
                synchronize_session=False
            )
            print(f"  Set is_active=0 for {completed_count} bets with status='completed'")
            
            # All bets with status='pending' or 'live' should have is_active=1
            active_count = db.session.query(Bet).filter(
                Bet.status.in_(['pending', 'live'])
            ).update(
                {'is_active': True},
                synchronize_session=False
            )
            print(f"  Set is_active=1 for {active_count} bets with status='pending'/'live'")
            
            db.session.commit()
            print("\n✅ Migration completed successfully!")
            
            # Show summary
            print("\n📊 Current bet distribution:")
            active_live = Bet.query.filter_by(is_active=True, is_archived=False).count()
            inactive_not_archived = Bet.query.filter_by(is_active=False, is_archived=False).count()
            archived = Bet.query.filter_by(is_archived=True).count()
            
            print(f"  Live Bets (is_active=1, is_archived=0): {active_live}")
            print(f"  Historical Bets (is_active=0, is_archived=0): {inactive_not_archived}")
            print(f"  Archived Bets (is_archived=1): {archived}")
            print(f"  Total: {Bet.query.count()}")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error during migration: {str(e)}")
            raise

if __name__ == '__main__':
    migrate_add_archive_columns()
