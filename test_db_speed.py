#!/usr/bin/env python3
"""Quick check - is the bottleneck the database or application code?"""
import psycopg2
import time

DATABASE_URL = 'postgresql://parlays_user:wgEpC1q34LIekYv6uelYqSThFdoy8xJT@dpg-d43b4iripnbc73bmuv5g-a.virginia-postgres.render.com/parlays'

def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Run ANALYZE to update stats for query planner
    print("Running ANALYZE...")
    cur.execute("ANALYZE")
    conn.commit()
    print("Done\n")
    
    # Count rows
    print("=== ROW COUNTS ===")
    for table in ['bets', 'bet_legs', 'players', 'teams']:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"  {table:<15} {count:>8} rows")
    
    # Test simple query speed
    print("\n=== QUERY SPEED TEST ===")
    
    # 1. Simple bet lookup
    start = time.time()
    cur.execute("SELECT * FROM bets WHERE status = 'active' LIMIT 10")
    cur.fetchall()
    print(f"  Get active bets: {(time.time() - start)*1000:.1f}ms")
    
    # 2. Bet with legs join
    start = time.time()
    cur.execute("""
        SELECT b.*, COUNT(bl.id) as leg_count
        FROM bets b
        LEFT JOIN bet_legs bl ON bl.bet_id = b.id
        WHERE b.status IN ('pending', 'active')
        GROUP BY b.id
        LIMIT 10
    """)
    cur.fetchall()
    print(f"  Get bets with leg count: {(time.time() - start)*1000:.1f}ms")
    
    # 3. Full bet + legs data (what the app actually needs)
    start = time.time()
    cur.execute("""
        SELECT b.*, bl.*
        FROM bets b
        LEFT JOIN bet_legs bl ON bl.bet_id = b.id
        WHERE b.status IN ('pending', 'active')
        LIMIT 100
    """)
    cur.fetchall()
    print(f"  Get bets with all legs: {(time.time() - start)*1000:.1f}ms")
    
    # 4. Historical query (typically slowest)
    start = time.time()
    cur.execute("""
        SELECT b.*, bl.*
        FROM bets b
        LEFT JOIN bet_legs bl ON bl.bet_id = b.id
        WHERE b.status IN ('completed', 'lost', 'won', 'void')
        ORDER BY b.created_at DESC
        LIMIT 50
    """)
    rows = cur.fetchall()
    elapsed_ms = (time.time() - start) * 1000
    print(f"  Get historical bets (50): {elapsed_ms:.1f}ms ({len(rows)} rows returned)")
    
    cur.close()
    conn.close()
    
    print("\n" + "="*50)
    if elapsed_ms > 1000:
        print("❌ DATABASE IS SLOW - queries taking >1s")
        print("   Indexes may not be helping. Need query optimization.")
    else:
        print("✅ DATABASE IS FAST - bottleneck is elsewhere")
        print("   Check application code, API calls, or network latency")

if __name__ == '__main__':
    main()
