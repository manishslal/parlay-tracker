"""
Database Migration Script: Add user_role Column
Purpose: Add user_role column to users table and set manishslal as admin
"""

from app import app, db
from models import User

def migrate_user_roles():
    """Add user_role column and set initial roles"""
    
    with app.app_context():
        print("Starting user_role migration...")
        
        # Check if column already exists
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('users')]
        
        if 'user_role' in columns:
            print("✓ user_role column already exists")
        else:
            print("Adding user_role column...")
            # Add column using raw SQL
            db.session.execute(
                "ALTER TABLE users ADD COLUMN user_role VARCHAR(20) DEFAULT 'user' NOT NULL"
            )
            db.session.commit()
            print("✓ user_role column added")
        
        # Set manishslal as admin
        print("\nSetting user roles...")
        manish_user = User.query.filter_by(username='manishslal').first()
        
        if manish_user:
            manish_user.user_role = 'admin'
            db.session.commit()
            print(f"✓ Set {manish_user.username} as admin")
        else:
            print("⚠ User 'manishslal' not found")
        
        # Set all other users as 'user' role
        other_users = User.query.filter(User.username != 'manishslal').all()
        updated_count = 0
        
        for user in other_users:
            if user.user_role != 'user':
                user.user_role = 'user'
                updated_count += 1
        
        if updated_count > 0:
            db.session.commit()
            print(f"✓ Set {updated_count} other users as 'user' role")
        else:
            print("✓ All other users already have 'user' role")
        
        # Show summary
        print("\n" + "="*50)
        print("ROLE SUMMARY")
        print("="*50)
        
        all_users = User.query.all()
        for user in all_users:
            role = user.user_role or 'user'
            icon = '👑' if role == 'admin' else '👤'
            print(f"{icon} {user.username:20} - {role}")
        
        print("="*50)
        print(f"\nTotal users: {len(all_users)}")
        print(f"Admins: {sum(1 for u in all_users if u.user_role == 'admin')}")
        print(f"Regular users: {sum(1 for u in all_users if u.user_role != 'admin')}")
        print("\n✅ Migration completed successfully!")

if __name__ == '__main__':
    migrate_user_roles()
