#!/usr/bin/env python3
"""
Export SQLite database to JSON for PostgreSQL migration
"""
import json
import os
from app import app, db
from models import User, Bet

def export_data():
    """Export all users and bets from SQLite to JSON"""
    with app.app_context():
        # Export Users
        users = User.query.all()
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'password_hash': user.password_hash,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'is_active': user.is_active
            })
        
        # Export Bets
        bets = Bet.query.all()
        bets_data = []
        for bet in bets:
            # Handle bet_date - might be string or date object
            bet_date_str = None
            if bet.bet_date:
                if hasattr(bet.bet_date, 'isoformat'):
                    bet_date_str = bet.bet_date.isoformat()
                else:
                    bet_date_str = str(bet.bet_date)
            
            bets_data.append({
                'id': bet.id,
                'user_id': bet.user_id,
                'bet_id': bet.bet_id,
                'status': bet.status,
                'bet_type': bet.bet_type,
                'betting_site': bet.betting_site,
                'bet_date': bet_date_str,
                'created_at': bet.created_at.isoformat() if bet.created_at else None,
                'updated_at': bet.updated_at.isoformat() if bet.updated_at else None,
                'is_active': bet.is_active,
                'is_archived': bet.is_archived,
                'api_fetched': bet.api_fetched,
                'bet_data': bet.bet_data  # Raw JSON string
            })
        
        # Save to JSON file
        export_data = {
            'users': users_data,
            'bets': bets_data,
            'export_timestamp': None,
            'counts': {
                'users': len(users_data),
                'bets': len(bets_data)
            }
        }
        
        # Use timestamp for filename
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'sqlite_export_{timestamp}.json'
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"\n✅ Export successful!")
        print(f"📁 File: {filename}")
        print(f"👥 Users exported: {len(users_data)}")
        print(f"🎲 Bets exported: {len(bets_data)}")
        print(f"\nUsers:")
        for user in users_data:
            print(f"  - {user['username']} ({user['email']})")
        
        return filename

if __name__ == '__main__':
    # Make sure we're using SQLite
    if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI']:
        print("⚠️  WARNING: Currently connected to PostgreSQL!")
        print("This script should run on SQLite database.")
        response = input("Continue anyway? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            exit(1)
    
    print(f"📊 Exporting from: {app.config['SQLALCHEMY_DATABASE_URI']}")
    export_data()
