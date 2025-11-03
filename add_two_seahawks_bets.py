#!/usr/bin/env python3
"""
Add Two Seahawks @ Commanders Bets - Shared by All Users
==========================================================
Bet 1: Zach Charbonnet Anytime TD (+115)
Bet 2: 4-Leg SGP (+166)

Both bets shared between: ManishSlal, EToteja, JTahiliani
"""

import os
import psycopg2
import json
from datetime import datetime

def add_two_seahawks_bets():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not set")
        return
    
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    print("\n" + "="*70)
    print("ADD TWO SEAHAWKS @ COMMANDERS BETS FOR ALL USERS")
    print("="*70)
    
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        now = datetime.now(datetime.UTC) if hasattr(datetime, 'UTC') else datetime.utcnow()
        
        # Get all three users (case-insensitive)
        users = {}
        for username in ['manishslal', 'etoteja', 'jtahiliani']:
            cur.execute("SELECT id, username FROM users WHERE LOWER(username) = LOWER(%s)", (username,))
            user = cur.fetchone()
            if user:
                users[username] = {'id': user[0], 'name': user[1]}
                print(f"✅ Found: {user[1]} (ID: {user[0]})")
            else:
                print(f"❌ Not found: {username}")
                return
        
        # Primary bettor will be jtahiliani (since these are his bets from the screenshots)
        primary_user = users['jtahiliani']
        
        print(f"\n[Bet 1/2] Zach Charbonnet Anytime TD Scorer")
        print("="*70)
        
        # Bet 1: Single bet - Zach Charbonnet Anytime TD
        bet1_data = {
            "name": "Zach Charbonnet",
            "type": "Single",
            "odds": "+115",
            "wager": 15.0,
            "returns": 32.25,
            "betting_site": "FanDuel",
            "bet_id": None,
            "legs": [
                {
                    "game_date": "2025-11-02",
                    "away": "Seattle Seahawks",
                    "home": "Washington Commanders",
                    "player": "Zach Charbonnet",
                    "target": 1,
                    "stat": "anytime_touchdown",
                    "stat_add": None,
                    "team": "Seattle Seahawks",
                    "position": "RB"
                }
            ],
            "bet_date": "2025-11-02",
            "sport": "NFL",
            "status": "pending"
        }
        
        print(f"  Type: {bet1_data['type']}")
        print(f"  Player: Zach Charbonnet - Anytime TD Scorer")
        print(f"  Wager: ${bet1_data['wager']} → ${bet1_data['returns']} ({bet1_data['odds']})")
        
        # Insert Bet 1
        cur.execute("""
            INSERT INTO bets (user_id, bet_id, status, bet_type, betting_site, bet_date,
                             created_at, updated_at, is_active, is_archived, api_fetched, bet_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (primary_user['id'], bet1_data.get('bet_id'), 'pending', bet1_data['type'], 
              'FanDuel', '2025-11-02', now, now, True, False, 'No', json.dumps(bet1_data)))
        
        bet1_id = cur.fetchone()[0]
        print(f"  ✅ Created Bet ID: {bet1_id}")
        
        # Share Bet 1 with all users
        for username, user_info in users.items():
            is_primary = username == 'jtahiliani'
            cur.execute("""
                INSERT INTO bet_users (bet_id, user_id, is_primary_bettor, created_at)
                VALUES (%s, %s, %s, %s)
            """, (bet1_id, user_info['id'], is_primary, now))
            print(f"  ✅ Shared with {user_info['name']}" + (" (primary)" if is_primary else ""))
        
        print(f"\n[Bet 2/2] 4-Leg SGP")
        print("="*70)
        
        # Bet 2: 4-Leg SGP
        bet2_data = {
            "name": "4 Pick Parlay",
            "type": "SGP",
            "odds": "+166",
            "wager": 30.0,
            "returns": 79.80,
            "betting_site": "FanDuel",
            "bet_id": None,
            "legs": [
                {
                    "game_date": "2025-11-02",
                    "away": "Seattle Seahawks",
                    "home": "Washington Commanders",
                    "player": "Kenneth Walker III",
                    "target": 40,
                    "stat": "rushing_yards",
                    "stat_add": "over",
                    "team": "Seattle Seahawks",
                    "position": "RB"
                },
                {
                    "game_date": "2025-11-02",
                    "away": "Seattle Seahawks",
                    "home": "Washington Commanders",
                    "player": "Tory Horton",
                    "target": 15,
                    "stat": "receiving_yards",
                    "stat_add": "over",
                    "team": "Washington Commanders",
                    "position": "WR"
                },
                {
                    "game_date": "2025-11-02",
                    "away": "Seattle Seahawks",
                    "home": "Washington Commanders",
                    "player": "Jayden Daniels",
                    "target": 220,
                    "stat": "passing_rushing_yards",
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
                }
            ],
            "bet_date": "2025-11-02",
            "sport": "NFL",
            "status": "pending"
        }
        
        print(f"  Type: {bet2_data['type']}")
        print(f"  Legs:")
        for i, leg in enumerate(bet2_data['legs'], 1):
            stat_display = leg['stat'].replace('_', ' ').title()
            addon = f" ({leg['stat_add']})" if leg.get('stat_add') else ""
            print(f"    {i}. {leg['player']} - {stat_display} {leg['target']}{addon}")
        print(f"  Wager: ${bet2_data['wager']} → ${bet2_data['returns']} ({bet2_data['odds']})")
        
        # Insert Bet 2
        cur.execute("""
            INSERT INTO bets (user_id, bet_id, status, bet_type, betting_site, bet_date,
                             created_at, updated_at, is_active, is_archived, api_fetched, bet_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (primary_user['id'], bet2_data.get('bet_id'), 'pending', bet2_data['type'],
              'FanDuel', '2025-11-02', now, now, True, False, 'No', json.dumps(bet2_data)))
        
        bet2_id = cur.fetchone()[0]
        print(f"  ✅ Created Bet ID: {bet2_id}")
        
        # Share Bet 2 with all users
        for username, user_info in users.items():
            is_primary = username == 'jtahiliani'
            cur.execute("""
                INSERT INTO bet_users (bet_id, user_id, is_primary_bettor, created_at)
                VALUES (%s, %s, %s, %s)
            """, (bet2_id, user_info['id'], is_primary, now))
            print(f"  ✅ Shared with {user_info['name']}" + (" (primary)" if is_primary else ""))
        
        conn.commit()
        
        print("\n" + "="*70)
        print("✅ SUCCESS! BOTH BETS CREATED")
        print("="*70)
        print(f"Bet 1 (Charbonnet TD): #{bet1_id}")
        print(f"Bet 2 (4-Leg SGP): #{bet2_id}")
        print(f"\nPrimary Bettor: {primary_user['name']}")
        print(f"Shared With: All 3 users (ManishSlal, EToteja, JTahiliani)")
        print(f"\nGame: Seattle Seahawks @ Washington Commanders")
        print(f"Time: Today 8:20 PM ET")
        print(f"\n🏈 Both bets visible in 'Today's Bets' tab for all users!")
        print(f"🏈 Will auto-move to 'Live Bets' when game starts")
        print(f"🏈 ESPN API will track all stats in real-time")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()

if __name__ == "__main__":
    add_two_seahawks_bets()
