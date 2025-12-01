"""
Inspect Production Database
Connects to production DB to investigate bet attribution.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import sys

# Production DB URL provided by user
PROD_DB_URL = "postgresql://parlays_user:wgEpC1q34LIekYv6uelYqSThFdoy8xJT@dpg-d43b4iripnbc73bmuv5g-a.virginia-postgres.render.com/parlays"

def inspect_prod():
    try:
        print(f"Connecting to production database...")
        conn = psycopg2.connect(PROD_DB_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. List all users
        print("\n--- ALL USERS ---")
        cur.execute("SELECT id, username, email, created_at FROM users ORDER BY id")
        users = cur.fetchall()
        for u in users:
            print(f"ID: {u['id']} | User: {u['username']} | Email: {u['email']}")
            
        # 2. Find Lakers/Celtics bets
        print("\n--- LAKERS/CELTICS BETS ---")
        query = """
            SELECT b.id as bet_id, b.user_id, u.username, 
                   bl.id as leg_id, bl.player_name, bl.home_team, bl.away_team, bl.game_date
            FROM bets b
            JOIN users u ON b.user_id = u.id
            JOIN bet_legs bl ON b.id = bl.bet_id
            WHERE bl.home_team ILIKE '%Celtics%' 
               OR bl.away_team ILIKE '%Celtics%' 
               OR bl.home_team ILIKE '%Lakers%' 
               OR bl.away_team ILIKE '%Lakers%'
            ORDER BY b.created_at DESC
            LIMIT 10
        """
        cur.execute(query)
        bets = cur.fetchall()
        
        if not bets:
            print("No Lakers or Celtics bets found.")
        else:
            for b in bets:
                print(f"Bet {b['bet_id']} | User: {b['user_id']} ({b['username']}) | "
                      f"Leg: {b['player_name']} ({b['away_team']} @ {b['home_team']})")
        
        conn.close()
        
    except Exception as e:
        print(f"Error connecting to production DB: {e}")

if __name__ == "__main__":
    inspect_prod()
