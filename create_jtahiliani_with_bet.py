#!/usr/bin/env python3
"""
Create jtahiliani user and add 3-Leg SGP bet - PRODUCTION
==========================================================
This script will:
1. Create jtahiliani user (if doesn't exist)
2. Add the Kyren Williams + Puka Nacua bet

Run this on Render shell.
"""

import os
import sys
import psycopg2
import json
from datetime import datetime

def create_user_and_bet():
    """Create user and add bet to production PostgreSQL database"""
    
    # Get DATABASE_URL from environment
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("\n❌ ERROR: DATABASE_URL environment variable not set!")
        return
    
    # Fix Render's postgres:// to postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    print("\n" + "="*60)
    print("CREATE USER AND ADD BET - PRODUCTION")
    print("="*60)
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        print("\n[Step 1/3] Checking for jtahiliani user...")
        
        # Check if user exists
        cur.execute("SELECT id, username FROM users WHERE username = %s", ('jtahiliani',))
        user = cur.fetchone()
        
        if user:
            user_id, username = user
            print(f"✅ User already exists: {username} (ID: {user_id})")
        else:
            # Create user
            print("Creating user 'jtahiliani'...")
            cur.execute("""
                INSERT INTO users (username, email, password_hash, created_at, is_active)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, username
            """, (
                'jtahiliani',
                'jtahiliani@example.com',
                '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5jtRfkKT7yjRe',  # Password: changeme123
                datetime.utcnow(),
                True
            ))
            user_id, username = cur.fetchone()
            conn.commit()
            print(f"✅ Created user: {username} (ID: {user_id})")
            print(f"   Password: changeme123")
        
        print(f"\n[Step 2/3] Creating bet data...")
        
        # Bet data structure
        bet_data = {
            "name": "3 Pick Parlay",
            "type": "SGP",
            "odds": "+297",
            "wager": 20.0,
            "returns": 79.40,
            "betting_site": "FanDuel",
            "bet_id": None,
            "boost": "+50% Parlay Boost",
            "legs": [
                {
                    "game_date": "2025-11-02",
                    "away": "New Orleans Saints",
                    "home": "Los Angeles Rams",
                    "player": "Kyren Williams",
                    "target": 1,
                    "stat": "anytime_touchdown",
                    "stat_add": None,
                    "team": "Los Angeles Rams",
                    "position": "RB"
                },
                {
                    "game_date": "2025-11-02",
                    "away": "New Orleans Saints",
                    "home": "Los Angeles Rams",
                    "player": "Kyren Williams",
                    "target": 70,
                    "stat": "rushing_yards",
                    "stat_add": "over",
                    "team": "Los Angeles Rams",
                    "position": "RB"
                },
                {
                    "game_date": "2025-11-02",
                    "away": "New Orleans Saints",
                    "home": "Los Angeles Rams",
                    "player": "Puka Nacua",
                    "target": 90,
                    "stat": "receiving_yards",
                    "stat_add": "over",
                    "team": "Los Angeles Rams",
                    "position": "WR"
                }
            ],
            "bet_date": "2025-11-02",
            "sport": "NFL",
            "status": "live"
        }
        
        print("\nBet Details:")
        print(f"  Name: {bet_data['name']}")
        print(f"  Type: {bet_data['type']}")
        print(f"  Wager: ${bet_data['wager']}")
        print(f"  To Pay: ${bet_data['returns']}")
        print(f"  Odds: {bet_data['odds']} (with {bet_data['boost']})")
        print(f"\n  Legs:")
        for i, leg in enumerate(bet_data['legs'], 1):
            stat_display = leg['stat'].replace('_', ' ').title()
            addon = f" ({leg['stat_add']})" if leg['stat_add'] else ""
            print(f"    {i}. {leg['player']} - {stat_display} {leg['target']}{addon}")
        
        print(f"\n[Step 3/3] Inserting bet into database...")
        
        # Insert bet into database
        insert_query = """
            INSERT INTO bets (
                user_id, bet_id, status, bet_type, betting_site, bet_date,
                created_at, updated_at, is_active, is_archived, api_fetched, bet_data
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            ) RETURNING id
        """
        
        cur.execute(insert_query, (
            user_id,
            None,  # bet_id
            'live',  # status
            'SGP',  # bet_type
            'FanDuel',  # betting_site
            '2025-11-02',  # bet_date
            datetime.utcnow(),  # created_at
            datetime.utcnow(),  # updated_at
            True,  # is_active
            False,  # is_archived
            'No',  # api_fetched (will fetch live data)
            json.dumps(bet_data)  # bet_data
        ))
        
        bet_id = cur.fetchone()[0]
        
        # Check if bet_users table exists (for many-to-many relationship)
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'bet_users'
            )
        """)
        
        if cur.fetchone()[0]:
            # Add to bet_users table
            cur.execute("""
                INSERT INTO bet_users (bet_id, user_id, is_primary_bettor, created_at)
                VALUES (%s, %s, %s, %s)
            """, (bet_id, user_id, True, datetime.utcnow()))
            print("✅ Added to bet_users table (many-to-many)")
        
        conn.commit()
        
        print("\n" + "="*60)
        print("✅ SUCCESS!")
        print("="*60)
        print(f"User: {username} (ID: {user_id})")
        print(f"Bet ID: {bet_id}")
        print(f"Status: live")
        print(f"Active: True")
        print(f"\nThe bet is now live and will fetch real-time stats from ESPN!")
        print(f"\nTo view:")
        print(f"1. Go to your Render URL")
        print(f"2. Login as 'jtahiliani' / 'changeme123'")
        print(f"3. Click 'Live Bets' tab")
        print(f"4. You'll see live stats from the Saints @ Rams game!")
        
        cur.close()
        conn.close()
        
    except psycopg2.Error as e:
        print("\n" + "="*60)
        print("❌ DATABASE ERROR")
        print("="*60)
        print(f"Error: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print("\n" + "="*60)
        print("❌ ERROR")
        print("="*60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_user_and_bet()
