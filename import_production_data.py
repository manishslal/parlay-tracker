#!/usr/bin/env python3
"""
Import Production Data to Local Database
Copies users and bets from Render to local PostgreSQL for testing
"""

import os
import sys

def import_from_production():
    """Import data from production database"""
    print("=" * 70)
    print("📥 IMPORTING DATA FROM PRODUCTION")
    print("=" * 70)
    
    # Get production DATABASE_URL
    prod_url = input("\n🔗 Enter your Render DATABASE_URL: ").strip()
    
    if not prod_url:
        print("❌ No DATABASE_URL provided")
        sys.exit(1)
    
    print("\n📊 Connecting to production database...")
    
    # Connect to production
    os.environ['DATABASE_URL'] = prod_url
    from app import app as prod_app, db as prod_db
    from models import User, Bet
    
    with prod_app.app_context():
        # Get production data
        prod_users = User.query.all()
        prod_bets = Bet.query.limit(10).all()  # Only get 10 bets for testing
        
        print(f"✅ Found {len(prod_users)} users and {len(prod_bets)} bets in production")
        
        # Store data
        users_data = []
        for user in prod_users:
            users_data.append({
                'username': user.username,
                'display_name': user.display_name,
                'email': user.email,
                'password_hash': user.password_hash,
                'is_active': user.is_active,
                'created_at': user.created_at
            })
        
        bets_data = []
        for bet in prod_bets:
            bets_data.append({
                'user_id': bet.user_id,
                'bet_id': bet.bet_id,
                'bet_type': bet.bet_type,
                'betting_site': bet.betting_site,
                'status': bet.status,
                'is_active': bet.is_active,
                'is_archived': bet.is_archived,
                'api_fetched': bet.api_fetched,
                'bet_data': bet.bet_data,
                'bet_date': bet.bet_date,
                'created_at': bet.created_at,
                'updated_at': bet.updated_at
            })
    
    # Now connect to local and insert
    print("\n📝 Importing to local database...")
    os.environ['DATABASE_URL'] = 'postgresql://manishslal@localhost/parlays_local'
    
    # Need to reload app with new DATABASE_URL
    from importlib import reload
    import app as app_module
    reload(app_module)
    from app import app as local_app, db as local_db
    from models import User as LocalUser, Bet as LocalBet
    
    with local_app.app_context():
        # Clear existing data
        LocalBet.query.delete()
        LocalUser.query.delete()
        local_db.session.commit()
        
        # Create user ID mapping (in case IDs are different)
        user_id_map = {}
        
        # Import users
        for user_data in users_data:
            user = LocalUser(
                username=user_data['username'],
                display_name=user_data['display_name'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                is_active=user_data['is_active'],
                created_at=user_data['created_at']
            )
            local_db.session.add(user)
            local_db.session.flush()  # Get the ID
            
            # Map old user_id to new user_id (in case they differ)
            # For now assume we're importing in order and IDs match
        
        local_db.session.commit()
        print(f"✅ Imported {len(users_data)} users")
        
        # Import bets
        for bet_data in bets_data:
            bet = LocalBet(
                user_id=bet_data['user_id'],
                bet_id=bet_data['bet_id'],
                bet_type=bet_data['bet_type'],
                betting_site=bet_data['betting_site'],
                status=bet_data['status'],
                is_active=bet_data['is_active'],
                is_archived=bet_data['is_archived'],
                api_fetched=bet_data['api_fetched'],
                bet_data=bet_data['bet_data'],
                bet_date=bet_data['bet_date'],
                created_at=bet_data['created_at'],
                updated_at=bet_data['updated_at']
            )
            local_db.session.add(bet)
        
        local_db.session.commit()
        print(f"✅ Imported {len(bets_data)} bets")
        
        print("\n" + "=" * 70)
        print("✅ IMPORT COMPLETE!")
        print("=" * 70)
        print(f"\n📊 Local database now has:")
        print(f"   Users: {LocalUser.query.count()}")
        print(f"   Bets: {LocalBet.query.count()}")
        print("\n💡 You can now test migrations on this local data!")

if __name__ == '__main__':
    import_from_production()
