#!/usr/bin/env python3
"""
Add Two Cowboys @ Cardinals Bets - Shared by ManishSlal and EToteja
====================================================================
Bet 1: Jake Ferguson 3-Leg SGP ($20 → $98.20, +391)
Bet 2: 8-Leg Multi-Player SGP ($20 → $95.00, +375)

Both bets shared between: ManishSlal (primary), EToteja (tailing)
"""

import os
import psycopg2
import json
from datetime import datetime

def add_cowboys_cardinals_bets():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not set")
        return
    
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    print("\n" + "="*70)
    print("ADD TWO COWBOYS @ CARDINALS BETS FOR MANISHSLAL & ETOTEJA")
    print("="*70)
    
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        now = datetime.now(datetime.UTC) if hasattr(datetime, 'UTC') else datetime.utcnow()
        
        # Get both users (case-insensitive)
        users = {}
        for username in ['manishslal', 'etoteja']:
            cur.execute("SELECT id, username FROM users WHERE LOWER(username) = LOWER(%s)", (username,))
            user = cur.fetchone()
            if user:
                users[username] = {'id': user[0], 'name': user[1]}
                print(f"✅ Found: {user[1]} (ID: {user[0]})")
            else:
                print(f"❌ Not found: {username}")
                return
        
        # Primary bettor will be ManishSlal
        primary_user = users['manishslal']
        
        print(f"\n[Bet 1/2] Jake Ferguson 3-Leg SGP")
        print("="*70)
        
        # Bet 1: Jake Ferguson 3-Leg SGP
        bet1_data = {
            "name": "Jake Ferguson SGP",
            "type": "SGP",
            "odds": "+391",
            "wager": 20.0,
            "returns": 98.20,
            "betting_site": "DraftKings",
            "bet_id": "DK638978114701876739",
            "legs": [
                {
                    "game_date": "2025-11-03",
                    "away": "Arizona Cardinals",
                    "home": "Dallas Cowboys",
                    "player": "Jake Ferguson",
                    "target": 1,
                    "stat": "anytime_touchdown",
                    "stat_add": None,
                    "team": "Dallas Cowboys",
                    "position": "TE"
                },
                {
                    "game_date": "2025-11-03",
                    "away": "Arizona Cardinals",
                    "home": "Dallas Cowboys",
                    "player": "Jake Ferguson",
                    "target": 50,
                    "stat": "receiving_yards",
                    "stat_add": "over",
                    "team": "Dallas Cowboys",
                    "position": "TE"
                },
                {
                    "game_date": "2025-11-03",
                    "away": "Arizona Cardinals",
                    "home": "Dallas Cowboys",
                    "player": "Jake Ferguson",
                    "target": 6,
                    "stat": "receptions",
                    "stat_add": "over",
                    "team": "Dallas Cowboys",
                    "position": "TE"
                }
            ],
            "bet_date": "2025-11-03",
            "sport": "NFL",
            "status": "pending"
        }
        
        print(f"  Type: {bet1_data['type']}")
        print(f"  Legs:")
        for i, leg in enumerate(bet1_data['legs'], 1):
            if leg['stat'] == 'anytime_touchdown':
                print(f"    {i}. {leg['player']} - Anytime TD Scorer")
            else:
                stat_display = leg['stat'].replace('_', ' ').title()
                addon = f" ({leg['stat_add']})" if leg.get('stat_add') else ""
                print(f"    {i}. {leg['player']} - {stat_display} {leg['target']}{addon}")
        print(f"  Wager: ${bet1_data['wager']} → ${bet1_data['returns']} ({bet1_data['odds']})")
        
        # Insert Bet 1
        cur.execute("""
            INSERT INTO bets (user_id, bet_id, status, bet_type, betting_site, bet_date,
                             created_at, updated_at, is_active, is_archived, api_fetched, bet_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (primary_user['id'], bet1_data.get('bet_id'), 'pending', bet1_data['type'], 
              'DraftKings', '2025-11-03', now, now, True, False, 'No', json.dumps(bet1_data)))
        
        bet1_id = cur.fetchone()[0]
        print(f"  ✅ Created Bet ID: {bet1_id}")
        
        # Share Bet 1 with both users
        for username, user_info in users.items():
            is_primary = username == 'manishslal'
            cur.execute("""
                INSERT INTO bet_users (bet_id, user_id, is_primary_bettor, created_at)
                VALUES (%s, %s, %s, %s)
            """, (bet1_id, user_info['id'], is_primary, now))
            print(f"  ✅ Shared with {user_info['name']}" + (" (primary)" if is_primary else " (tailing)"))
        
        print(f"\n[Bet 2/2] 8-Leg Multi-Player SGP")
        print("="*70)
        
        # Bet 2: 8-Leg Multi-Player SGP
        bet2_data = {
            "name": "8 Pick SGP",
            "type": "SGP",
            "odds": "+375",
            "wager": 20.0,
            "returns": 95.0,
            "betting_site": "DraftKings",
            "bet_id": "DK638978106602969999",
            "legs": [
                {
                    "game_date": "2025-11-03",
                    "away": "Arizona Cardinals",
                    "home": "Dallas Cowboys",
                    "player": "Dak Prescott",
                    "target": 200,
                    "stat": "passing_yards",
                    "stat_add": "over",
                    "team": "Dallas Cowboys",
                    "position": "QB"
                },
                {
                    "game_date": "2025-11-03",
                    "away": "Arizona Cardinals",
                    "home": "Dallas Cowboys",
                    "player": "Trey McBride",
                    "target": 40,
                    "stat": "receiving_yards",
                    "stat_add": "over",
                    "team": "Arizona Cardinals",
                    "position": "TE"
                },
                {
                    "game_date": "2025-11-03",
                    "away": "Arizona Cardinals",
                    "home": "Dallas Cowboys",
                    "player": "Jake Ferguson",
                    "target": 25,
                    "stat": "receiving_yards",
                    "stat_add": "over",
                    "team": "Dallas Cowboys",
                    "position": "TE"
                },
                {
                    "game_date": "2025-11-03",
                    "away": "Arizona Cardinals",
                    "home": "Dallas Cowboys",
                    "player": "Marvin Harrison Jr.",
                    "target": 25,
                    "stat": "receiving_yards",
                    "stat_add": "over",
                    "team": "Arizona Cardinals",
                    "position": "WR"
                },
                {
                    "game_date": "2025-11-03",
                    "away": "Arizona Cardinals",
                    "home": "Dallas Cowboys",
                    "player": "Jacoby Brissett",
                    "target": 180,
                    "stat": "passing_yards",
                    "stat_add": "over",
                    "team": "Arizona Cardinals",
                    "position": "QB"
                },
                {
                    "game_date": "2025-11-03",
                    "away": "Arizona Cardinals",
                    "home": "Dallas Cowboys",
                    "player": "George Pickens",
                    "target": 40,
                    "stat": "receiving_yards",
                    "stat_add": "over",
                    "team": "Dallas Cowboys",
                    "position": "WR"
                },
                {
                    "game_date": "2025-11-03",
                    "away": "Arizona Cardinals",
                    "home": "Dallas Cowboys",
                    "player": "Javonte Williams",
                    "target": 40,
                    "stat": "rushing_yards",
                    "stat_add": "over",
                    "team": "Dallas Cowboys",
                    "position": "RB"
                },
                {
                    "game_date": "2025-11-03",
                    "away": "Arizona Cardinals",
                    "home": "Dallas Cowboys",
                    "player": "CeeDee Lamb",
                    "target": 50,
                    "stat": "receiving_yards",
                    "stat_add": "over",
                    "team": "Dallas Cowboys",
                    "position": "WR"
                }
            ],
            "bet_date": "2025-11-03",
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
              'DraftKings', '2025-11-03', now, now, True, False, 'No', json.dumps(bet2_data)))
        
        bet2_id = cur.fetchone()[0]
        print(f"  ✅ Created Bet ID: {bet2_id}")
        
        # Share Bet 2 with both users
        for username, user_info in users.items():
            is_primary = username == 'manishslal'
            cur.execute("""
                INSERT INTO bet_users (bet_id, user_id, is_primary_bettor, created_at)
                VALUES (%s, %s, %s, %s)
            """, (bet2_id, user_info['id'], is_primary, now))
            print(f"  ✅ Shared with {user_info['name']}" + (" (primary)" if is_primary else " (tailing)"))
        
        # Commit all changes
        conn.commit()
        
        print("\n" + "="*70)
        print("✅ SUCCESS!")
        print("="*70)
        print(f"Added 2 bets:")
        print(f"  1. Jake Ferguson SGP (Bet ID: {bet1_id})")
        print(f"  2. 8 Pick SGP (Bet ID: {bet2_id})")
        print(f"\nShared with:")
        print(f"  - {users['manishslal']['name']} (Primary Bettor)")
        print(f"  - {users['etoteja']['name']} (Tailing)")
        print(f"\nGame: Arizona Cardinals @ Dallas Cowboys")
        print(f"Date: Nov 3, 2025 @ 8:15 PM ET")
        print(f"\nBoth users will see these bets in their Live Bets view!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if 'conn' in locals():
            conn.rollback()
        import traceback
        traceback.print_exc()
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    add_cowboys_cardinals_bets()
