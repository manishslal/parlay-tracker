"""
Check what score data exists in JSON bet_data for historical bets.
"""

import os
import sys
import json
import psycopg2
from psycopg2.extras import RealDictCursor

def check_json_scores():
    """Check what scores are in JSON bet_data."""
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        return
    
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    if 'sslmode' not in database_url:
        database_url += '?sslmode=require'
    
    print("Connecting to database...\n")
    conn = psycopg2.connect(database_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get some completed bets
        cur.execute("""
            SELECT id, bet_data, status, created_at::date as bet_date
            FROM bets
            WHERE bet_data IS NOT NULL
            AND status IN ('completed', 'lost', 'won')
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        bets = cur.fetchall()
        print(f"Checking {len(bets)} recent completed bets:\n")
        
        total_legs = 0
        legs_with_scores = 0
        
        for bet in bets:
            bet_id = bet['id']
            bet_data = bet['bet_data']
            
            if isinstance(bet_data, str):
                try:
                    bet_data = json.loads(bet_data)
                except:
                    continue
            
            legs = bet_data.get('legs', [])
            total_legs += len(legs)
            
            print(f"Bet {bet_id} ({bet['bet_date']}) - {len(legs)} legs:")
            
            for i, leg in enumerate(legs):
                player = leg.get('player', 'N/A')
                home_score = leg.get('homeScore')
                away_score = leg.get('awayScore')
                home = leg.get('home', 'N/A')
                away = leg.get('away', 'N/A')
                current = leg.get('current')
                status = leg.get('status')
                
                if home_score is not None or away_score is not None:
                    legs_with_scores += 1
                    print(f"  ✅ Leg {i+1}: {player}")
                    print(f"     {away} {away_score} - {home_score} {home}")
                    print(f"     Current: {current}, Status: {status}")
                else:
                    print(f"  ❌ Leg {i+1}: {player} - NO SCORES in JSON")
                    print(f"     Game: {away} @ {home}")
                    print(f"     Current: {current}, Status: {status}")
            print()
        
        print(f"{'='*60}")
        print(f"Summary:")
        print(f"  Total legs checked: {total_legs}")
        print(f"  Legs with scores in JSON: {legs_with_scores}")
        print(f"  Legs without scores: {total_legs - legs_with_scores}")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    check_json_scores()
