#!/usr/bin/env python3
"""
Fix script for invalid password hashes on Render
Run this on Render to reset passwords for users with corrupted hashes
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User

def fix_invalid_passwords():
    """Fix users with invalid password hashes by resetting their passwords"""
    with app.app_context():
        users = User.query.all()
        print(f"Checking {len(users)} users for invalid password hashes...")

        fixed_count = 0
        for user in users:
            hash_value = user.password_hash

            # Check if hash is valid bcrypt format
            is_valid = False
            try:
                import bcrypt
                # Try to check against a dummy password to validate hash structure
                bcrypt.checkpw(b'test_validation', hash_value.encode('utf-8'))
                is_valid = True
            except ValueError:
                is_valid = False
            except Exception:
                is_valid = False

            if not is_valid:
                print(f"❌ User {user.username} has invalid password hash")
                print(f"   Hash: {hash_value[:50]}{'...' if len(hash_value) > 50 else ''}")

                # Reset password to a temporary one
                temp_password = f"temp_{user.username}_123"
                user.set_password(temp_password)
                fixed_count += 1

                print(f"   ✅ Reset password to: {temp_password}")
                print(f"   🔑 New hash: {user.password_hash[:30]}...")
            else:
                print(f"✅ User {user.username} has valid password hash")

        if fixed_count > 0:
            db.session.commit()
            print(f"\n✅ Fixed {fixed_count} users with invalid password hashes")
            print("   Users should log in with their temporary passwords and change them immediately")
        else:
            print("\n✅ All users have valid password hashes")

if __name__ == "__main__":
    fix_invalid_passwords()