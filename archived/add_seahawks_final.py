#!/usr/bin/env python3
"""
Add Seahawks @ Commanders Bet - Using Existing Users
=====================================================
Uses the existing ManishSlal and EToteja users (proper capitalization)
"""

import os
import psycopg2
import json
from datetime import datetime

def add_seahawks_bet():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not set")
        return
    
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    print("\n" + "="*70)
    print("ADD SEAHAWKS @ COMMANDERS BET FOR MANISHSLAL & ETOTEJA")
    print("="*70)
    
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        now = datetime.now(datetime.UTC) if hasattr(datetime, 'UTC') else datetime.utcnow()
        
        # Find ManishSlal (note the capitalization!)
        cur.execute("SELECT id, username FROM users WHERE LOWER(username) = LOWER(%s)", ('manishslal',))
        primary = cur.fetchone()
        
        # Find EToteja
        cur.execute("SELECT id, username FROM users WHERE LOWER(username) = LOWER(%s)", ('etoteja',))
        shared = cur.fetchone()
        
        if not primary:
            print("❌ ManishSlal not found")
            return
        
        print(f"✅ Primary: {primary[1]} (ID: {primary[0]})")
        
        if shared:
            print(f"✅ Shared: {shared[1]} (ID: {shared[0]})")
        
        # Check if bet already exists
        cur.execute("SELECT COUNT(*) FROM bets WHERE bet_id = %s", ('O/0240915/0000066',))
        if cur.fetchone()[0] > 0:
            print("\n⚠️  This bet already exists!")
            print("Check your 'Today's Bets' or 'Live Bets' tab")
            return
        
        bet_data = {
            "name": "Same Game Parlay",
            "type": "SGP",
            "odds": "+251",
            "wager": 10.0,
            "returns": 35.18,
            "betting_site": "FanDuel",
            "bet_id": "O/0240915/0000066",
            "legs": [
                {"game_date": "2025-11-02", "away": "Seattle Seahawks", "home": "Washington Commanders",
                 "player": "Sam Darnold", "target": 200, "stat": "passing_yards", "stat_add": "over",
                 "team": "Seattle Seahawks", "position": "QB"},
                {"game_date": "2025-11-02", "away": "Seattle Seahawks", "home": "Washington Commanders",
                 "player": "Sam Darnold", "target": 200, "stat": "passing_yards_alt", "stat_add": "over",
                 "team": "Seattle Seahawks", "position": "QB"},
                {"game_date": "2025-11-02", "away": "Seattle Seahawks", "home": "Washington Commanders",
                 "player": "Jayden Daniels", "target": 225, "stat": "passing_rushing_yards", "stat_add": "over",
                 "team": "Washington Commanders", "position": "QB"},
                {"game_date": "2025-11-02", "away": "Seattle Seahawks", "home": "Washington Commanders",
                 "player": "Jayden Daniels", "target": 1, "stat": "passing_touchdowns", "stat_add": "over",
                 "team": "Washington Commanders", "position": "QB"},
                {"game_date": "2025-11-02", "away": "Seattle Seahawks", "home": "Washington Commanders",
                 "player": "Jaxon Smith-Njigba", "target": 70, "stat": "receiving_yards", "stat_add": "over",
                 "team": "Seattle Seahawks", "position": "WR"},
                {"game_date": "2025-11-02", "away": "Seattle Seahawks", "home": "Washington Commanders",
                 "player": "Zach Ertz", "target": 15, "stat": "receiving_yards", "stat_add": "over",
                 "team": "Washington Commanders", "position": "TE"},
                {"game_date": "2025-11-02", "away": "Seattle Seahawks", "home": "Washington Commanders",
                 "player": "Deebo Samuel", "target": 4, "stat": "receptions", "stat_add": "over",
                 "team": "Seattle Seahawks", "position": "WR"},
                {"game_date": "2025-11-02", "away": "Seattle Seahawks", "home": "Washington Commanders",
                 "player": "Jacory Croskey-Merritt", "target": 25, "stat": "rushing_yards", "stat_add": "over",
                 "team": "Washington Commanders", "position": "RB"}
            ],
            "bet_date": "2025-11-02",
            "sport": "NFL",
            "status": "pending"
        }
        
        print(f"\n✅ Creating bet: {bet_data['name']} (8 legs, ${bet_data['wager']} → ${bet_data['returns']})")
        
        cur.execute("""
            INSERT INTO bets (user_id, bet_id, status, bet_type, betting_site, bet_date,
                             created_at, updated_at, is_active, is_archived, api_fetched, bet_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (primary[0], bet_data['bet_id'], 'pending', 'SGP', 'FanDuel', '2025-11-02',
              now, now, True, False, 'No', json.dumps(bet_data)))
        
        bet_id = cur.fetchone()[0]
        
        # Add to bet_users
        cur.execute("INSERT INTO bet_users (bet_id, user_id, is_primary_bettor, created_at) VALUES (%s, %s, %s, %s)",
                   (bet_id, primary[0], True, now))
        
        if shared:
            cur.execute("INSERT INTO bet_users (bet_id, user_id, is_primary_bettor, created_at) VALUES (%s, %s, %s, %s)",
                       (bet_id, shared[0], False, now))
        
        conn.commit()
        
        print(f"\n✅ SUCCESS! Bet ID: {bet_id}")
        print(f"✅ Visible to: {primary[1]}" + (f" and {shared[1]}" if shared else ""))
        print(f"\n🏈 Check 'Today's Bets' tab to see it!")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_seahawks_bet()
