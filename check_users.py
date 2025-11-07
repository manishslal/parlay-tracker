#!/usr/bin/env python3
"""Check what users exist in the database"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User

def check_users():
    with app.app_context():
        users = User.query.all()
        
        print(f"\n=== Found {len(users)} users in database ===\n")
        
        for user in users:
            print(f"ID: {user.id}")
            print(f"Username: '{user.username}'")
            print(f"Email: {user.email}")
            print(f"Active: {user.is_active}")
            print(f"Created: {user.created_at}")
            print("-" * 50)

if __name__ == '__main__':
    check_users()
