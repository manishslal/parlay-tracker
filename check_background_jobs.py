#!/usr/bin/env python3
"""
Check if background jobs are running on Render
"""
import requests
import json
from datetime import datetime, timedelta
import psycopg2

DATABASE_URL = 'postgresql://parlays_user:wgEpC1q34LIekYv6uelYqSThFdoy8xJT@dpg-d43b4iripnbc73bmuv5g-a.virginia-postgres.render.com/parlays'

def check_recent_updates():
    """Check when bet_legs were last updated by background jobs"""
    print("=" * 70)
    print("CHECKING BACKGROUND JOB ACTIVITY")
    print("=" * 70)
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Check recent updates to bet_legs
    cur.execute("""
        SELECT 
            COUNT(*) as total_legs,
            MAX(updated_at) as last_update,
            COUNT(CASE WHEN updated_at > NOW() - INTERVAL '5 minutes' THEN 1 END) as updated_last_5min,
            COUNT(CASE WHEN updated_at > NOW() - INTERVAL '1 hour' THEN 1 END) as updated_last_hour
        FROM bet_legs
        WHERE achieved_value IS NOT NULL
    """)
    
    result = cur.fetchone()
    print(f"\n📊 Bet Legs Update Stats:")
    print(f"  Total legs with data: {result[0]}")
    print(f"  Last update: {result[1]}")
    print(f"  Updated in last 5 min: {result[2]}")
    print(f"  Updated in last hour: {result[3]}")
    
    if result[1]:
        time_since = datetime.now() - result[1].replace(tzinfo=None)
        print(f"  Time since last update: {time_since}")
        
        if time_since > timedelta(minutes=5):
            print(f"\n⚠️  WARNING: No updates in {time_since}!")
            print(f"  → Background job 'live_bet_updates' may not be running")
            print(f"  → Should run every 1 minute")
        else:
            print(f"\n✅ Background jobs appear to be running (recent updates)")
    
    # Check for Ayton specifically
    cur.execute("""
        SELECT bl.id, bl.player_name, bl.stat_type, bl.target_value,
               bl.achieved_value, bl.game_status, bl.updated_at,
               b.status as bet_status
        FROM bet_legs bl
        JOIN bets b ON b.id = bl.bet_id
        WHERE bl.player_name ILIKE '%ayton%'
        ORDER BY bl.updated_at DESC
        LIMIT 5
    """)
    
    ayton_legs = cur.fetchall()
    if ayton_legs:
        print(f"\n📊 Ayton Leg Status:")
        for leg in ayton_legs:
            print(f"\n  Leg ID: {leg[0]}")
            print(f"    Player: {leg[1]}")
            print(f"    Stat: {leg[2]}")
            print(f"    Target: {leg[3]}, Achieved: {leg[4]}")
            print(f"    Game Status: {leg[5]}")
            print(f"    Bet Status: {leg[7]}")
            print(f"    Last Updated: {leg[6]}")
            
            if leg[4] == 0:
                print(f"    ⚠️  Achieved value is 0 - may not be getting ESPN data")
    
    cur.close()
    conn.close()

def check_scheduler_logs():
    """Instructions for checking scheduler logs on Render"""
    print("\n" + "=" * 70)
    print("HOW TO CHECK SCHEDULER LOGS ON RENDER")
    print("=" * 70)
    print("""
1. Go to Render Dashboard
2. Click on your backend service
3. Go to "Logs" tab
4. Search for these patterns:

   ✅ JOB SCHEDULED:
      "Adding job 'live_bet_updates' to scheduler"
   
   ✅ JOB RUNNING:
      "[LIVE-UPDATE] Starting live bet leg update check..."
      "[LIVE-UPDATE] Updating X live/pending bets"
   
   ✅ JOB COMPLETED:
      "[LIVE-UPDATE] ✓ Updated X legs across Y live bets"
   
   ⚠️  JOB ERRORS:
      "[LIVE-UPDATE] Error updating live bet"
      
5. If you don't see these logs:
   - Background jobs may not be starting
   - Check if APScheduler is enabled
   - Verify Gunicorn workers are running
    """)

if __name__ == '__main__':
    check_recent_updates()
    check_scheduler_logs()
    
    print("\n" + "=" * 70)
    print("DIAGNOSIS COMPLETE")
    print("=" * 70)
