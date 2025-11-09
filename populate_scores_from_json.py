"""
Populate home_score and away_score in bet_legs table from JSON bet_data.

For historical bets, the scores are stored in the bet_data JSON blob but not
in the bet_legs table. This script extracts scores from JSON and populates
the bet_legs table so the frontend can display them.
"""

import os
import sys
import json
import psycopg2
from psycopg2.extras import RealDictCursor

def populate_scores():
    """Extract scores from JSON bet_data and populate bet_legs table."""
    
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        print("Usage: DATABASE_URL='postgresql://...' python populate_scores_from_json.py")
        return
    
    # Convert postgres:// to postgresql:// for psycopg2
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    print("Connecting to database...")
    conn = psycopg2.connect(database_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get all bets with their JSON data
        cur.execute("""
            SELECT id, bet_data, status
            FROM bets
            WHERE bet_data IS NOT NULL
            AND status IN ('completed', 'lost', 'won')
            ORDER BY id
        """)
        
        bets = cur.fetchall()
        print(f"Found {len(bets)} completed bets with JSON data\n")
        
        updated_legs = 0
        bets_processed = 0
        
        for bet in bets:
            bet_id = bet['id']
            bet_data = bet['bet_data']
            
            # Parse JSON if it's a string
            if isinstance(bet_data, str):
                try:
                    bet_data = json.loads(bet_data)
                except:
                    print(f"⚠️  Bet {bet_id}: Could not parse JSON")
                    continue
            
            legs = bet_data.get('legs', [])
            if not legs:
                continue
            
            bets_processed += 1
            print(f"Processing Bet {bet_id} ({len(legs)} legs)...")
            
            for i, json_leg in enumerate(legs):
                # Get scores from JSON
                home_score = json_leg.get('homeScore')
                away_score = json_leg.get('awayScore')
                
                # Skip if no scores in JSON
                if home_score is None and away_score is None:
                    continue
                
                # Get the corresponding bet_leg record
                cur.execute("""
                    SELECT id, player_name, home_score, away_score
                    FROM bet_legs
                    WHERE bet_id = %s
                    ORDER BY leg_order
                    LIMIT 1 OFFSET %s
                """, (bet_id, i))
                
                bet_leg = cur.fetchone()
                if not bet_leg:
                    print(f"  ⚠️  No bet_leg found for leg {i}")
                    continue
                
                leg_id = bet_leg['id']
                player_name = bet_leg['player_name']
                
                # Check if scores are already populated
                if bet_leg['home_score'] is not None or bet_leg['away_score'] is not None:
                    continue
                
                # Update scores
                cur.execute("""
                    UPDATE bet_legs
                    SET home_score = %s, away_score = %s, updated_at = NOW()
                    WHERE id = %s
                """, (home_score, away_score, leg_id))
                
                updated_legs += 1
                print(f"  ✅ {player_name}: {home_score} - {away_score}")
            
            print()
        
        # Commit changes
        conn.commit()
        
        print(f"\n{'='*60}")
        print(f"✅ Successfully updated {updated_legs} bet legs")
        print(f"   Processed {bets_processed} bets")
        print(f"{'='*60}")
        
        # Show sample results
        cur.execute("""
            SELECT bl.player_name, bl.bet_type, bl.home_score, bl.away_score, 
                   bl.home_team, bl.away_team, b.status
            FROM bet_legs bl
            JOIN bets b ON bl.bet_id = b.id
            WHERE bl.home_score IS NOT NULL
            AND b.status = 'completed'
            LIMIT 5
        """)
        
        samples = cur.fetchall()
        if samples:
            print("\nSample results:")
            for s in samples:
                print(f"  {s['player_name']} ({s['bet_type']}): "
                      f"{s['away_team']} {s['away_score']} - {s['home_score']} {s['home_team']}")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    populate_scores()
