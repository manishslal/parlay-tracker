"""
database.py - Migration and DB setup utilities for Parlay Tracker
"""
from models import db, User
from sqlalchemy import inspect

def run_migrations_once(app):
    """
    Run startup migrations to ensure DB schema is up to date.
    Adds user_role column if missing and sets admin user.
    """
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            if 'user_role' not in columns:
                print("[MIGRATION] Adding user_role column...")
                db.session.execute(db.text("ALTER TABLE users ADD COLUMN user_role VARCHAR(20) DEFAULT 'user' NOT NULL"))
                db.session.commit()
                print("[MIGRATION] ✓ user_role column added")
                manish_user = User.query.filter_by(username='manishslal').first()
                if manish_user:
                    manish_user.user_role = 'admin'
                    db.session.commit()
                    print(f"[MIGRATION] ✓ Set {manish_user.username} as admin")
                print("[MIGRATION] ✓ Migration completed")
            else:
                print("[MIGRATION] ✓ user_role column already exists")
        except Exception as e:
            print(f"[MIGRATION] Migration check failed: {e}")
            try:
                db.session.rollback()
            except Exception:
                pass
