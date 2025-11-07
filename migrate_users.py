#!/usr/bin/env python3
"""
Update users to add display_name field and normalize usernames.
- Usernames become lowercase (for consistent lookups)
- Display names preserve the original capitalization (for UI)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User

def migrate_users():
    with app.app_context():
        print("\n=== User Migration: Add display_name and normalize usernames ===\n")
        
        # Add display_name column if it doesn't exist
        try:
            # Try to access display_name - if it fails, we need to add the column
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            if 'display_name' not in columns:
                print("Adding display_name column to users table...")
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE users ADD COLUMN display_name VARCHAR(80)'))
                    conn.commit()
                print("✓ Column added successfully\n")
            else:
                print("✓ display_name column already exists\n")
        except Exception as e:
            print(f"Error checking/adding column: {e}\n")
        
        # Define user mappings: current_username -> (new_username, display_name)
        user_mappings = {
            'manishslal': ('manishslal', 'ManishSLal'),
            'ManishSLal': ('manishslal', 'ManishSLal'),
            'EToteja': ('etoteja', 'EToteja'),
            'etoteja': ('etoteja', 'EToteja'),
            'JTahiliani': ('jtahiliani', 'JTahiliani'),
            'jtahiliani': ('jtahiliani', 'JTahiliani'),
        }
        
        users = User.query.all()
        print(f"Found {len(users)} users to process:\n")
        
        updated_count = 0
        for user in users:
            old_username = user.username
            
            # Find mapping (case-insensitive)
            mapping = user_mappings.get(old_username.lower())
            
            if mapping:
                new_username, display_name = mapping
                
                # Check if we need to update
                if user.username != new_username or user.display_name != display_name:
                    print(f"Updating user ID {user.id}:")
                    print(f"  Username: '{user.username}' → '{new_username}'")
                    print(f"  Display Name: '{user.display_name}' → '{display_name}'")
                    
                    user.username = new_username
                    user.display_name = display_name
                    updated_count += 1
                else:
                    print(f"User ID {user.id} already up to date: {user.username} / {user.display_name}")
            else:
                # User not in our mapping - just set display_name if missing
                if not user.display_name:
                    print(f"Setting display_name for unmapped user ID {user.id}: {user.username}")
                    user.display_name = user.username
                    updated_count += 1
        
        if updated_count > 0:
            print(f"\n✓ Committing {updated_count} updates to database...")
            db.session.commit()
            print("✓ Migration completed successfully!\n")
        else:
            print("\n✓ No updates needed - all users already migrated!\n")
        
        # Show final state
        print("=== Final User State ===\n")
        users = User.query.all()
        for user in users:
            print(f"ID: {user.id}")
            print(f"Username: '{user.username}'")
            print(f"Display Name: '{user.display_name}'")
            print(f"Email: {user.email}")
            print("-" * 50)

if __name__ == '__main__':
    migrate_users()
