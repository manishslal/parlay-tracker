#!/usr/bin/env python3
"""
Diagnostic script to check why a specific bet wasn't moved to historical
"""
import psycopg2
from datetime import datetime, timedelta

DATABASE_URL = 'postgresql://parlays_user:wgEpC1q34LIekYv6uelYqSThFdoy8xJT@dpg-d43b4iripnbc73bmuv5g-a.virginia-postgres.render.com/parlays'

def check_stuck_live_bets():
    """Find bets that should be historical but are still marked as live"""
    
    print("=" * 70)
    print("CHECKING FOR STUCK LIVE BETS")
    print("=" * 70)
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Find all bets with status='live' that have old game dates
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    cur.execute("""
        SELECT DISTINCT b.id, b.status, b.created_at,
               MIN(bl.game_date) as earliest_game,
               MAX(bl.game_date) as latest_game,
               COUNT(bl.id) as num_legs,
               COUNT(CASE WHEN bl.status = 'won' THEN 1 END) as won_legs,
               COUNT(CASE WHEN bl.status = 'lost' THEN 1 END) as lost_legs,
               COUNT(CASE WHEN bl.status = 'pending' THEN 1 END) as pending_legs,
               COUNT(CASE WHEN bl.game_status = 'STATUS_FINAL' THEN 1 END) as final_games
        FROM bets b
        JOIN bet_legs bl ON bl.bet_id = b.id
        WHERE b.status = 'live'
          AND bl.game_date < %s
        GROUP BY b.id, b.status, b.created_at
        ORDER BY latest_game DESC
    """, (yesterday,))
    
    stuck_bets = cur.fetchall()
    
    if not stuck_bets:
        print("\n✅ No stuck live bets found!")
        cur.close()
        conn.close()
        return
    
    print(f"\n⚠️  Found {len(stuck_bets)} bet(s) still marked as 'live' with games from yesterday or earlier:\n")
    
    for bet in stuck_bets:
        bet_id, status, created_at, earliest, latest, num_legs, won, lost, pending, final = bet
        
        print(f"🔍 Bet ID: {bet_id}")
        print(f"   Status: {status}")
        print(f"   Game Date Range: {earliest} to {latest}")
        print(f"   \n   Legs: {num_legs} total")
        print(f"      Won: {won}")
        print(f"      Lost: {lost}")
        print(f"      Pending: {pending}")
        print(f"   \n   Games: {final}/{num_legs} are FINAL")
        
        # Diagnose why it wasn't moved
        print(f"\n   📋 Diagnosis:")
        
        if pending > 0:
            print(f"      ⚠️  {pending} leg(s) still have status='pending'")
            print(f"         → Automation requires all legs to be won/lost")
        
        if final < num_legs:
            print(f"      ⚠️  {num_legs - final} game(s) not marked as STATUS_FINAL")
            print(f"         → Automation may be waiting for final status")
        
        # Check individual legs
        cur.execute("""
            SELECT leg_order, player_name, stat_type, target_value, 
                   achieved_value, status, game_status, sport
            FROM bet_legs
            WHERE bet_id = %s
            ORDER BY leg_order
        """, (bet_id,))
        
        legs = cur.fetchall()
        print(f"\n   📊 Leg Details:")
        for leg in legs:
            order, player, stat, target, achieved, leg_status, game_status, sport = leg
            print(f"      Leg {order}: {player or 'Team Bet'} - {stat}")
            print(f"         Target: {target}, Achieved: {achieved}")
            print(f"         Status: {leg_status}, Game: {game_status}")
            print(f"         Sport: {sport}")
            
            if leg_status == 'pending' and game_status == 'STATUS_FINAL':
                print(f"         ⚠️  BUG: Game is FINAL but leg still pending!")
            
            if achieved is None and game_status == 'STATUS_FINAL':
                print(f"         ⚠️  BUG: Game is FINAL but no achieved value!")
        
        print("\n" + "-" * 70 + "\n")
    
    cur.close()
    conn.close()

def check_automation_logs():
    """Check when automations last ran"""
    print("\n" + "=" * 70)
    print("AUTOMATION STATUS")
    print("=" * 70)
    print("""
To verify automations are running, check Render logs for:

1. Scheduler started:
   "[SCHEDULER] Configured APScheduler with persistent SQLAlchemy job store"

2. Jobs running:
   "[SCHEDULER] Running auto_move_bets_no_live_legs"
   "[COMPLETED-BET-UPDATES] Checking for completed bets..."

3. Bets being moved:
   "Moving bet XXX from live to completed"
   
If you don't see these logs, the scheduler isn't running properly.
    """)

if __name__ == '__main__':
    check_stuck_live_bets()
    check_automation_logs()
    
    print("\n" + "=" * 70)
    print("DIAGNOSIS COMPLETE")
    print("=" * 70)
