#!/usr/bin/env python3
"""
Update existing usernames to use proper capitalization
This preserves the case-insensitive login while displaying proper names
"""
from app import app, db
from models import User

# Mapping of current usernames to proper capitalization
USERNAME_CAPITALIZATION = {
    'manishslal': 'ManishSlal',
    'etoteja': 'EToteja',
    'jtahiliani': 'JTahiliani'
}

def update_username_capitalization():
    """Update usernames to use proper capitalization"""
    
    with app.app_context():
        print("="*80)
        print("UPDATING USERNAME CAPITALIZATION")
        print("="*80 + "\n")
        
        updated_count = 0
        
        for old_username, new_username in USERNAME_CAPITALIZATION.items():
            # Find user (case-insensitive)
            user = User.query.filter(
                db.func.lower(User.username) == old_username.lower()
            ).first()
            
            if user:
                old_display = user.username
                user.username = new_username
                print(f"✅ Updated: '{old_display}' → '{new_username}'")
                updated_count += 1
            else:
                print(f"⚠️  User '{old_username}' not found")
        
        if updated_count > 0:
            db.session.commit()
            print(f"\n{'='*80}")
            print(f"✅ Updated {updated_count} usernames")
            print("="*80)
            
            print("\nVerification:")
            all_users = User.query.all()
            for user in all_users:
                print(f"  - Username: {user.username}")
                print(f"    Email: {user.email}")
                print(f"    Login works with: {user.username.lower()}, {user.username.upper()}, {user.username}")
                print()
        else:
            print(f"\n{'='*80}")
            print("ℹ️  No usernames to update")
            print("="*80)

if __name__ == '__main__':
    update_username_capitalization()
