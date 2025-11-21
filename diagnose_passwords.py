#!/usr/bin/env python3
"""
Diagnostic script to check user password hashes on Render
Run this on Render to inspect password hash issues
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User

def diagnose_password_hashes():
    """Check all user password hashes for validity"""
    with app.app_context():
        users = User.query.all()
        print(f"Found {len(users)} users in database:")

        for user in users:
            hash_value = user.password_hash
            print(f"\nUser: {user.username} (ID: {user.id})")
            print(f"  Email: {user.email}")
            print(f"  Hash length: {len(hash_value)}")
            print(f"  Hash preview: {hash_value[:30]}{'...' if len(hash_value) > 30 else ''}")

            # Check if hash starts with bcrypt prefix
            if hash_value.startswith('$2b$') or hash_value.startswith('$2a$'):
                print("  ✅ Valid bcrypt hash format")
            else:
                print("  ❌ Invalid hash format - not a bcrypt hash!")

            # Try to validate the hash structure
            try:
                import bcrypt
                # This will raise ValueError if the hash is invalid
                bcrypt.checkpw(b'test', hash_value.encode('utf-8'))
                print("  ✅ Hash structure is valid")
            except ValueError as e:
                print(f"  ❌ Hash structure invalid: {e}")
            except Exception as e:
                print(f"  ⚠️  Unexpected error checking hash: {e}")

if __name__ == "__main__":
    diagnose_password_hashes()