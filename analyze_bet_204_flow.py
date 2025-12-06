#!/usr/bin/env python3
"""
Deep Analysis of Bet 204 Data Flow Issues
"""
import psycopg2
from datetime import datetime

DATABASE_URL = 'postgresql://parlays_user:wgEpC1q34LIekYv6uelYqSThFdoy8xJT@dpg-d43b4iripnbc73bmuv5g-a.virginia-postgres.render.com/parlays'

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("=" * 80)
print("BET 204: DATA FLOW ANALYSIS")
print("=" * 80)

# Get bet creation time
cur.execute("SELECT created_at, bet_date FROM bets WHERE id = 204")
bet_created = cur.fetchone()
print(f"\n📅 Bet Timeline:")
print(f"   Created: {bet_created[0]}")
print(f"   Bet Date: {bet_created[1]}")

# Check all legs with their key fields
cur.execute("""
    SELECT 
        leg_order,
        player_name,
        stat_type,
        home_team,
        away_team,
        game_id,
        game_date,
        game_status,
        status,
        achieved_value,
        created_at,
        updated_at
    FROM bet_legs
    WHERE bet_id = 204
    ORDER BY id
""")

legs = cur.fetchall()
print(f"\n🔍 Detailed Leg Analysis ({len(legs)} legs):\n")

tbd_count = 0
null_count = 0
populated_count = 0
has_game_id_count = 0

for i, leg in enumerate(legs, 1):
    order, player, stat, home, away, game_id, date, game_status, status, achieved, created, updated = leg
    
    print(f"Leg {i}:")
    print(f"  Player: {player}")
    print(f"  Teams: {away or 'NULL'} @ {home or 'NULL'}")
    print(f"  Game ID: {game_id or 'NULL'}")
    print(f"  Game Status: {game_status}")
    print(f"  Leg Status: {status}")
    print(f"  Achieved: {achieved}")
    print(f"  Created: {created}")
    print(f"  Updated: {updated}")
    
    # Track patterns
    if away == 'TBD':
        tbd_count += 1
        print(f"  ⚠️  Away team = TBD")
    elif away is None:
        null_count += 1
        print(f"  ⚠️  Away team = NULL")
    else:
        populated_count += 1
    
    if game_id:
        has_game_id_count += 1
        if away == 'TBD' or away is None:
            print(f"  🐛 BUG: Has game_id but missing away_team!")
    
    print()

print("=" * 80)
print("PATTERN SUMMARY:")
print("=" * 80)
print(f"Legs with TBD away_team: {tbd_count}")
print(f"Legs with NULL away_team: {null_count}")  
print(f"Legs with populated away_team: {populated_count}")
print(f"Legs with game_id: {has_game_id_count}")

print("\n" + "=" * 80)
print("AUTOMATION TIMING (from Render logs):")
print("=" * 80)
print("""
From logs at 19:14:11 UTC (created at 23:39:23):
- Bet created: 2025-12-05 23:39:23 (11:39 PM ET)
- Scheduler start: 2025-12-06 19:13:57 (2:13 PM ET next day)
  
Jobs and schedules:
1. populate_missing_game_ids - Every 2 minutes
2. populate_missing_player_data - Every 3 minutes  
3. live_bet_updates - Every 1 minute
4. auto_move_bets_no_live_legs - Every 5 minutes

TIMELINE:
- 11:39 PM: Bet 204 created (OCR?)
- 11:39 PM - 2:13 PM: Scheduler NOT RUNNING (14+ hours!)
- 2:13 PM: Scheduler starts
- 2:14 PM: Jobs run

PROBLEM: Games on 12/5 already finished by time scheduler started!
""")

cur.close()
conn.close()

print("\n" + "=" * 80)
print("ROOT CAUSES IDENTIFIED:")
print("=" * 80)
print("""
1. SCHEDULER DOWNTIME
   - Bet created at 11:39 PM on 12/5
   - Scheduler didn't start until 2:13 PM on 12/6 (14+ hours later)
   - Games finished before automations could run

2. "TBD" SOURCE
   - Need to find where "TBD" string comes from
   - Likely from OCR or initial bet creation
   - Should be NULL instead

3. INCOMPLETE DATA POPULATION
   - Some legs got game_id, others didn't
   - Some legs got team names from ESPN, others kept TBD
   - Inconsistent ESPN API matching

4. STATUS LOGIC
   - Bet marked as 'pending' instead of 'lost'
   - Need to check where status is calculated
""")
