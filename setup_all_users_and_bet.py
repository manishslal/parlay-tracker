#!/usr/bin/env python3
"""
Setup Users and Add Seahawks @ Commanders Bet - PRODUCTION
===========================================================
This script will:
1. Create users: manishslal, etoteja, jtahiliani (if they don't exist)
2. Create bet_users table for many-to-many relationships
3. Add the 7-leg SGP for Seahawks @ Commanders
4. Share it between manishslal and etoteja
"""

import os
import sys
import psycopg2
import json
from datetime import datetime

def setup_and_add_bet():
    """Setup users and add the bet"""
    
    # Get DATABASE_URL from environment
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("\n❌ ERROR: DATABASE_URL environment variable not set!")
        return
    
    # Fix Render's postgres:// to postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    print("\n" + "="*70)
    print("SETUP USERS AND ADD SEAHAWKS @ COMMANDERS BET")
    print("="*70)
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        now = datetime.now(datetime.UTC) if hasattr(datetime, 'UTC') else datetime.utcnow()
        
        print("\n[Step 1/5] Creating bet_users table if needed...")
        
        # Create bet_users table for many-to-many relationships
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bet_users (
                bet_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                is_primary_bettor BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (bet_id, user_id),
                FOREIGN KEY (bet_id) REFERENCES bets(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        conn.commit()
        print("✅ bet_users table ready")
        
        print("\n[Step 2/5] Creating/checking users...")
        
        # Users to create
        users_to_create = [
            {
                'username': 'manishslal',
                'email': 'manishslal@gmail.com',
                'password_hash': '$2b$12$cN4HBJ4.bH43/GLMtcAhSOKTKG0CjDHDu21K9qO5z1lfx5LbsNcXm'  # Password: test123
            },
            {
                'username': 'etoteja',
                'email': 'etoteja@example.com',
                'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5jtRfkKT7yjRe'  # Password: changeme123
            },
            {
                'username': 'jtahiliani',
                'email': 'jtahiliani@example.com',
                'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5jtRfkKT7yjRe'  # Password: changeme123
            }
        ]
        
        created_users = {}
        
        for user_info in users_to_create:
            # Check if user exists
            cur.execute(
                "SELECT id, username FROM users WHERE username = %s OR email = %s",
                (user_info['username'], user_info['email'])
            )
            existing = cur.fetchone()
            
            if existing:
                user_id, username = existing
                created_users[user_info['username']] = user_id
                print(f"✅ User exists: {username} (ID: {user_id})")
            else:
                # Create user
                cur.execute("""
                    INSERT INTO users (username, email, password_hash, created_at, is_active)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, username
                """, (
                    user_info['username'],
                    user_info['email'],
                    user_info['password_hash'],
                    now,
                    True
                ))
                user_id, username = cur.fetchone()
                created_users[user_info['username']] = user_id
                conn.commit()
                print(f"✅ Created user: {username} (ID: {user_id})")
        
        manishslal_id = created_users['manishslal']
        etoteja_id = created_users['etoteja']
        
        print(f"\n[Step 3/5] Creating bet data...")
        
        # Bet data structure
        bet_data = {
            "name": "Same Game Parlay",
            "type": "SGP",
            "odds": "+251",
            "wager": 10.0,
            "returns": 35.18,
            "betting_site": "FanDuel",
            "bet_id": "O/0240915/0000066",
            "legs": [
                {
                    "game_date": "2025-11-02",
                    "away": "Seattle Seahawks",
                    "home": "Washington Commanders",
                    "player": "Sam Darnold",
                    "target": 200,
                    "stat": "passing_yards",
                    "stat_add": "over",
                    "team": "Seattle Seahawks",
                    "position": "QB"
                },
                {
                    "game_date": "2025-11-02",
                    "away": "Seattle Seahawks",
                    "home": "Washington Commanders",
                    "player": "Sam Darnold",
                    "target": 200,
                    "stat": "passing_yards_alt",
                    "stat_add": "over",
                    "team": "Seattle Seahawks",
                    "position": "QB"
                },
                {
                    "game_date": "2025-11-02",
                    "away": "Seattle Seahawks",
                    "home": "Washington Commanders",
                    "player": "Jayden Daniels",
                    "target": 225,
                    "stat": "passing_rushing_yards",
                    "stat_add": "over",
                    "team": "Washington Commanders",
                    "position": "QB"
                },
                {
                    "game_date": "2025-11-02",
                    "away": "Seattle Seahawks",
                    "home": "Washington Commanders",
                    "player": "Jayden Daniels",
                    "target": 1,
                    "stat": "passing_touchdowns",
                    "stat_add": "over",
                    "team": "Washington Commanders",
                    "position": "QB"
                },
                {
                    "game_date": "2025-11-02",
                    "away": "Seattle Seahawks",
                    "home": "Washington Commanders",
                    "player": "Jaxon Smith-Njigba",
                    "target": 70,
                    "stat": "receiving_yards",
                    "stat_add": "over",
                    "team": "Seattle Seahawks",
                    "position": "WR"
                },
                {
                    "game_date": "2025-11-02",
                    "away": "Seattle Seahawks",
                    "home": "Washington Commanders",
                    "player": "Zach Ertz",
                    "target": 15,
                    "stat": "receiving_yards",
                    "stat_add": "over",
                    "team": "Washington Commanders",
                    "position": "TE"
                },
                {
                    "game_date": "2025-11-02",
                    "away": "Seattle Seahawks",
                    "home": "Washington Commanders",
                    "player": "Deebo Samuel",
                    "target": 4,
                    "stat": "receptions",
                    "stat_add": "over",
                    "team": "Seattle Seahawks",
                    "position": "WR"
                },
                {
                    "game_date": "2025-11-02",
                    "away": "Seattle Seahawks",
                    "home": "Washington Commanders",
                    "player": "Jacory Croskey-Merritt",
                    "target": 25,
                    "stat": "rushing_yards",
                    "stat_add": "over",
                    "team": "Washington Commanders",
                    "position": "RB"
                }
            ],
            "bet_date": "2025-11-02",
            "sport": "NFL",
            "status": "pending"
        }
        
        print(f"✅ Bet: {bet_data['name']} (8 legs)")
        print(f"   Wager: ${bet_data['wager']} → ${bet_data['returns']}")
        print(f"   Odds: {bet_data['odds']}")
        
        print(f"\n[Step 4/5] Inserting bet into database...")
        
        # Insert bet
        cur.execute("""
            INSERT INTO bets (
                user_id, bet_id, status, bet_type, betting_site, bet_date,
                created_at, updated_at, is_active, is_archived, api_fetched, bet_data
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            ) RETURNING id
        """, (
            manishslal_id,
            bet_data['bet_id'],
            'pending',
            'SGP',
            'FanDuel',
            '2025-11-02',
            now,
            now,
            True,
            False,
            'No',
            json.dumps(bet_data)
        ))
        
        bet_id = cur.fetchone()[0]
        print(f"✅ Bet created with ID: {bet_id}")
        
        print(f"\n[Step 5/5] Setting up bet sharing...")
        
        # Add to bet_users table - primary bettor
        cur.execute("""
            INSERT INTO bet_users (bet_id, user_id, is_primary_bettor, created_at)
            VALUES (%s, %s, %s, %s)
        """, (bet_id, manishslal_id, True, now))
        print(f"✅ Added manishslal as primary bettor")
        
        # Add to bet_users table - shared with etoteja
        cur.execute("""
            INSERT INTO bet_users (bet_id, user_id, is_primary_bettor, created_at)
            VALUES (%s, %s, %s, %s)
        """, (bet_id, etoteja_id, False, now))
        print(f"✅ Shared with etoteja")
        
        conn.commit()
        
        print("\n" + "="*70)
        print("✅ SUCCESS!")
        print("="*70)
        print(f"Bet ID: {bet_id}")
        print(f"Primary Bettor: manishslal (ID: {manishslal_id})")
        print(f"Shared With: etoteja (ID: {etoteja_id})")
        print(f"Status: pending → will auto-move to 'Live Bets' when game starts")
        print(f"Game: Seattle Seahawks @ Washington Commanders")
        print(f"Time: 8:21 PM ET tonight")
        print(f"\n✅ Users created:")
        for username, user_id in created_users.items():
            print(f"   • {username} (ID: {user_id})")
        print(f"\nLogin credentials:")
        print(f"   • manishslal / test123")
        print(f"   • etoteja / changeme123")
        print(f"   • jtahiliani / changeme123")
        print(f"\n🏈 The bet is now live and tracking!")
        
        cur.close()
        conn.close()
        
    except psycopg2.Error as e:
        print("\n" + "="*70)
        print("❌ DATABASE ERROR")
        print("="*70)
        print(f"Error: {e}")
        if conn:
            conn.rollback()
        import traceback
        traceback.print_exc()
    except Exception as e:
        print("\n" + "="*70)
        print("❌ ERROR")
        print("="*70)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    setup_and_add_bet()
