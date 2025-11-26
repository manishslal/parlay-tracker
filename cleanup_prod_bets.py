"""
Cleanup Production Bets
Removes duplicate Lakers/Celtics bets for user 1, keeping only the most recent one.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import sys

# Production DB URL provided by user
PROD_DB_URL = "postgresql://parlays_user:wgEpC1q34LIekYv6uelYqSThFdoy8xJT@dpg-d43b4iripnbc73bmuv5g-a.virginia-postgres.render.com/parlays"

def cleanup_bets():
    try:
        print(f"Connecting to production database...")
        conn = psycopg2.connect(PROD_DB_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Find all Lakers/Celtics bets for user 1
        print("\n--- FINDING DUPLICATE BETS ---")
        query = """
            SELECT DISTINCT b.id, b.created_at, b.user_id
            FROM bets b
            JOIN bet_legs bl ON b.id = bl.bet_id
            WHERE b.user_id = 1
              AND (bl.home_team ILIKE '%Celtics%' 
                OR bl.away_team ILIKE '%Celtics%' 
                OR bl.home_team ILIKE '%Lakers%' 
                OR bl.away_team ILIKE '%Lakers%')
            ORDER BY b.created_at DESC
        """
        cur.execute(query)
        bets = cur.fetchall()
        
        if not bets:
            print("No Lakers/Celtics bets found for user 1.")
            return

        print(f"Found {len(bets)} bets matching criteria.")
        
        if len(bets) <= 1:
            print("Only 1 or 0 bets found. No duplicates to delete.")
            return

        # 2. Identify bets to keep and delete
        # Sorted by created_at DESC, so index 0 is the most recent
        bet_to_keep = bets[0]
        bets_to_delete = bets[1:]
        
        print(f"\nKEEPING (Most Recent):")
        print(f"  Bet ID: {bet_to_keep['id']} | Created: {bet_to_keep['created_at']}")
        
        print(f"\nDELETING ({len(bets_to_delete)} bets):")
        delete_ids = []
        for b in bets_to_delete:
            print(f"  Bet ID: {b['id']} | Created: {b['created_at']}")
            delete_ids.append(b['id'])
            
        if not delete_ids:
            print("Nothing to delete.")
            return

        # 3. Execute Deletion
        print(f"\n--- EXECUTING DELETION ---")
        
        # Delete legs first (though cascade might handle it, explicit is safer)
        legs_query = "DELETE FROM bet_legs WHERE bet_id = ANY(%s)"
        cur.execute(legs_query, (delete_ids,))
        legs_deleted = cur.rowcount
        print(f"Deleted {legs_deleted} bet legs.")
        
        # Delete bets
        bets_query = "DELETE FROM bets WHERE id = ANY(%s)"
        cur.execute(bets_query, (delete_ids,))
        bets_deleted = cur.rowcount
        print(f"Deleted {bets_deleted} bets.")
        
        conn.commit()
        print("\nSUCCESS: Cleanup complete.")
        
        conn.close()
        
    except Exception as e:
        print(f"Error connecting to production DB: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()

if __name__ == "__main__":
    cleanup_bets()
