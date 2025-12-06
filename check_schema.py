#!/usr/bin/env python3
"""Check production database schema"""
import psycopg2

DATABASE_URL = 'postgresql://parlays_user:wgEpC1q34LIekYv6uelYqSThFdoy8xJT@dpg-d43b4iripnbc73bmuv5g-a.virginia-postgres.render.com/parlays'

def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Check players table columns
    print("=== PLAYERS TABLE COLUMNS ===")
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'players'
        ORDER BY ordinal_position
    """)
    for row in cur.fetchall():
        print(f"  {row[0]:<30} {row[1]}")
    
    # Check teams table exists
    print("\n=== TEAMS TABLE COLUMNS ===")
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'teams'
        ORDER BY ordinal_position
    """)
    for row in cur.fetchall():
        print(f"  {row[0]:<30} {row[1]}")
    
    # Check games table exists
    print("\n=== GAMES TABLE ===")
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'games'
        )
    """)
    exists = cur.fetchone()[0]
    print(f"  Games table exists: {exists}")
    
    if exists:
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'games'
            ORDER BY ordinal_position
        """)
        for row in cur.fetchall():
            print(f"  {row[0]:<30} {row[1]}")
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
