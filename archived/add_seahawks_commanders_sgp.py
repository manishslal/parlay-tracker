#!/usr/bin/env python3
"""
Add 7-Leg SGP for Seahawks @ Commanders - PRODUCTION
=====================================================
This bet will be visible to manishslal and etoteja (shared bet).

Bet Details:
- 7-leg Same Game Parlay (SGP)
- $10 wager → $35.18 payout (+251 odds)
- Game: Seattle Seahawks @ Washington Commanders (Nov 2, 2025 8:21 PM ET)
"""

import os
import sys
import psycopg2
import json
from datetime import datetime

def add_seahawks_commanders_bet():
    """Add the 7-leg SGP bet and share it with manishslal and etoteja"""
    
    # Get DATABASE_URL from environment
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("\n❌ ERROR: DATABASE_URL environment variable not set!")
        return
    
    # Fix Render's postgres:// to postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    print("\n" + "="*70)
    print("ADD 7-LEG SGP FOR SEAHAWKS @ COMMANDERS")
    print("="*70)
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        print("\n[Step 1/4] Finding users...")
        
        # Find manishslal (primary bettor)
        cur.execute("SELECT id, username FROM users WHERE username = %s", ('manishslal',))
        primary_user = cur.fetchone()
        
        if not primary_user:
            print("❌ ERROR: User 'manishslal' not found!")
            return
        
        primary_user_id, primary_username = primary_user
        print(f"✅ Primary bettor: {primary_username} (ID: {primary_user_id})")
        
        # Find etoteja (shared viewer)
        cur.execute("SELECT id, username FROM users WHERE username = %s", ('etoteja',))
        shared_user = cur.fetchone()
        
        if shared_user:
            shared_user_id, shared_username = shared_user
            print(f"✅ Shared with: {shared_username} (ID: {shared_user_id})")
        else:
            print("⚠️  User 'etoteja' not found - bet will only be visible to manishslal")
            shared_user = None
        
        print(f"\n[Step 2/4] Creating bet data...")
        
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
                    "stat": "passing_yards",
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
        
        print("\nBet Details:")
        print(f"  Name: {bet_data['name']}")
        print(f"  Type: {bet_data['type']}")
        print(f"  Game: Seattle Seahawks @ Washington Commanders")
        print(f"  Wager: ${bet_data['wager']}")
        print(f"  To Pay: ${bet_data['returns']}")
        print(f"  Odds: {bet_data['odds']}")
        print(f"  Bet ID: {bet_data['bet_id']}")
        print(f"\n  Legs ({len(bet_data['legs'])}):")
        for i, leg in enumerate(bet_data['legs'], 1):
            stat_display = leg['stat'].replace('_', ' ').title()
            addon = f" ({leg['stat_add']})" if leg.get('stat_add') else ""
            print(f"    {i}. {leg['player']} - {stat_display} {leg['target']}{addon}")
        
        print(f"\n[Step 3/4] Inserting bet into database...")
        
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
        
        now = datetime.now(datetime.UTC) if hasattr(datetime, 'UTC') else datetime.utcnow()
        
        cur.execute(insert_query, (
            primary_user_id,
            bet_data['bet_id'],
            'pending',  # status (game hasn't started yet)
            'SGP',  # bet_type
            'FanDuel',  # betting_site
            '2025-11-02',  # bet_date
            now,  # created_at
            now,  # updated_at
            True,  # is_active (will be in Today's Bets until game starts)
            False,  # is_archived
            'No',  # api_fetched (will fetch when game starts)
            json.dumps(bet_data)  # bet_data
        ))
        
        bet_id = cur.fetchone()[0]
        print(f"✅ Bet created with ID: {bet_id}")
        
        print(f"\n[Step 4/4] Setting up bet sharing...")
        
        # Check if bet_users table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'bet_users'
            )
        """)
        
        if cur.fetchone()[0]:
            # Add primary bettor to bet_users
            cur.execute("""
                INSERT INTO bet_users (bet_id, user_id, is_primary_bettor, created_at)
                VALUES (%s, %s, %s, %s)
            """, (bet_id, primary_user_id, True, now))
            print(f"✅ Added {primary_username} as primary bettor")
            
            # Add etoteja as shared viewer if user exists
            if shared_user:
                cur.execute("""
                    INSERT INTO bet_users (bet_id, user_id, is_primary_bettor, created_at)
                    VALUES (%s, %s, %s, %s)
                """, (bet_id, shared_user_id, False, now))
                print(f"✅ Shared with {shared_username}")
        
        conn.commit()
        
        print("\n" + "="*70)
        print("✅ SUCCESS!")
        print("="*70)
        print(f"Bet ID: {bet_id}")
        print(f"Primary Bettor: {primary_username}")
        if shared_user:
            print(f"Shared With: {shared_username}")
        print(f"Status: pending (will move to live when game starts)")
        print(f"Game Time: 8:21 PM ET tonight")
        print(f"\nThe bet will:")
        print(f"  • Show in 'Today's Bets' tab until game starts")
        print(f"  • Auto-move to 'Live Bets' when game begins")
        print(f"  • Fetch real-time stats from ESPN during the game")
        print(f"  • Move to 'Historical' when complete or if any leg loses")
        print(f"\nBoth {primary_username} and {shared_username if shared_user else 'N/A'} can view it!")
        
        cur.close()
        conn.close()
        
    except psycopg2.Error as e:
        print("\n" + "="*70)
        print("❌ DATABASE ERROR")
        print("="*70)
        print(f"Error: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print("\n" + "="*70)
        print("❌ ERROR")
        print("="*70)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_seahawks_commanders_bet()
