#!/usr/bin/env python3
"""Analyze why queries are still slow despite indexes"""
import psycopg2
import time

DATABASE_URL = 'postgresql://parlays_user:wgEpC1q34LIekYv6uelYqSThFdoy8xJT@dpg-d43b4iripnbc73bmuv5g-a.virginia-postgres.render.com/parlays'

def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # First, ANALYZE tables to update statistics so indexes are used
    print("=== ANALYZING TABLES (updating query planner statistics) ===")
    for table in ['bets', 'bet_legs', 'players', 'teams']:
        print(f"Analyzing {table}...")
        cur.execute(f"ANALYZE {table}")
    conn.commit()
    print("✅ Analysis complete\n")
    
    # Check table sizes
    print("=== TABLE SIZES ===")
    cur.execute("""
        SELECT 
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
            n_live_tup as row_count
        FROM pg_stat_user_tables
        WHERE schemaname = 'public'
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
    """)
    for row in cur.fetchall():
        print(f"  {row[0]:<20} {row[1]:<15} {row[2]:>10} rows")
    
    # Test a common query with EXPLAIN ANALYZE
    print("\n=== TESTING QUERY PERFORMANCE ===")
    print("Query: Get all bet_legs for user's bets")
    
    # Find a user_id
    cur.execute("SELECT id FROM users LIMIT 1")
    user_id = cur.fetchone()[0]
    
    start = time.time()
    cur.execute(f"""
        EXPLAIN ANALYZE
        SELECT bl.* 
        FROM bet_legs bl
        JOIN bets b ON b.id = bl.bet_id
        WHERE b.user_id = {user_id}
        AND b.status IN ('pending', 'active', 'completed')
        ORDER BY b.created_at DESC
        LIMIT 50
    """)
    explain_output = cur.fetchall()
    elapsed = time.time() - start
    
    print(f"\nQuery took: {elapsed:.3f}s")
    print("\nExecution plan:")
    for line in explain_output:
        print(f"  {line[0]}")
    
    # Check if indexes are being used
    print("\n=== CHECKING INDEX USAGE ===")
    cur.execute("""
        SELECT 
            schemaname,
            tablename,
            indexname,
            idx_scan as times_used,
            idx_tup_read as tuples_read,
            idx_tup_fetch as tuples_fetched
        FROM pg_stat_user_indexes
        WHERE schemaname = 'public'
        AND indexname LIKE 'idx_%'
        ORDER BY idx_scan DESC
        LIMIT 20
    """)
    
    print(f"\n{'Index':<40} {'Scans':<10} {'Tuples Read':<15} {'Tuples Fetched'}")
    print("-" * 80)
    for row in cur.fetchall():
        print(f"{row[2]:<40} {row[3]:<10} {row[4]:<15} {row[5]}")
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
