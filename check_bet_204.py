#!/usr/bin/env python3
"""Check details of bet 204"""
import psycopg2
from datetime import datetime

DATABASE_URL = 'postgresql://parlays_user:wgEpC1q34LIekYv6uelYqSThFdoy8xJT@dpg-d43b4iripnbc73bmuv5g-a.virginia-postgres.render.com/parlays'

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("=" * 70)
print("BET 204 DETAILS")
print("=" * 70)

# Get bet details
cur.execute("""
    SELECT id, status, is_active, is_archived, created_at, bet_date
    FROM bets
    WHERE id = 204
""")
bet = cur.fetchone()
print(f"\n📋 Bet Info:")
print(f"   ID: {bet[0]}")
print(f"   Status: {bet[1]}")
print(f"   Is Active: {bet[2]}")
print(f"   Is Archived: {bet[3]}")
print(f"   Created: {bet[4]}")
print(f"   Bet Date: {bet[5]}")

# Get leg details
cur.execute("""
    SELECT leg_order, player_name, stat_type, target_value, achieved_value,
           status, game_status, game_date, home_team, away_team
    FROM bet_legs
    WHERE bet_id = 204
    ORDER BY leg_order
""")

legs = cur.fetchall()
print(f"\n📊 Legs ({len(legs)} total):")
for leg in legs:
    order, player, stat, target, achieved, status, game_status, date, home, away = leg
    print(f"\n   Leg {order}: {player or 'Team Bet'}")
    print(f"      Stat: {stat}")
    print(f"      Target: {target}, Achieved: {achieved}")
    print(f"      Status: {status}")
    print(f"      Game: {away} @ {home} on {date}")
    print(f"      Game Status: {game_status}")
    
    if game_status == 'STATUS_FINAL' and status == 'pending':
        print(f"      ⚠️  BUG: Game is FINAL but leg still pending!")

cur.close()
conn.close()

print("\n" + "=" * 70)
print("DIAGNOSIS:")
print("=" * 70)
print("""
This bet is stuck because:
1. Bet status = 'pending' (should be 'live' or 'completed')
2. auto_move_bets_no_live_legs ONLY checks status='live'
3. Game ended yesterday but bet never transitioned

FIX NEEDED:
- Update automation to also check status='pending' 
- OR manually move this bet to historical
""")
