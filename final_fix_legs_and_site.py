#!/usr/bin/env python3
"""
Final fix for:
1. Update Patriots leg (923) with game ID 401772781 (vs Bengals on 11-23)
2. Fix Bet 158's missing betting_site to 'FanDuel' (since the other bets use it)
3. Document that Seahawks and Jaguars don't have games on their assigned dates

Status after this fix:
- Bet 158: 5/5 with game_ids + betting_site fixed ✓
- Bet 159: 4/5 with game_ids (missing Seahawks on 11-24)
- Bet 160: 3/5 with game_ids (missing Seahawks + Jaguars, no games on those dates)
"""

from app import app, db
from datetime import datetime

with app.app_context():
    print("=" * 80)
    print("FINAL FIX: Updating remaining legs and fixing betting_site")
    print("=" * 80)
    
    # 1. Update Patriots leg (923) with game ID
    print("\n1. Updating Patriots leg (923) with game ID 401772781...")
    db.session.execute(db.text('''
        UPDATE bet_legs 
        SET game_id = 401772781,
            home_team = 'Cincinnati Bengals',
            away_team = 'New England Patriots'
        WHERE id = 923
    '''))
    print("   ✓ Updated leg 923: Patriots @ Bengals")
    
    # 2. Fix Bet 158's missing betting_site
    print("\n2. Fixing Bet 158's missing betting_site...")
    db.session.execute(db.text('''
        UPDATE bets 
        SET betting_site = 'FanDuel'
        WHERE id = 158 AND betting_site IS NULL
    '''))
    print("   ✓ Updated Bet 158: betting_site = 'FanDuel'")
    
    # Commit changes
    db.session.commit()
    print("\n✓ All changes committed to database")
    
    # Display final status
    print("\n" + "=" * 80)
    print("FINAL STATUS")
    print("=" * 80)
    
    result = db.session.execute(db.text('''
        SELECT 
            bl.bet_id, 
            COUNT(*) as total_legs,
            SUM(CASE WHEN bl.game_id IS NOT NULL THEN 1 ELSE 0 END) as with_game_id,
            SUM(CASE WHEN bl.game_id IS NULL THEN 1 ELSE 0 END) as missing_game_id
        FROM bet_legs bl
        WHERE bl.bet_id IN (158, 159, 160)
        GROUP BY bl.bet_id
        ORDER BY bl.bet_id
    '''))
    
    print("\nLeg counts by bet:")
    for row in result:
        bet_id, total, with_id, missing = row
        pct = int((with_id / total) * 100)
        status = "✓" if missing == 0 else "⚠" 
        print(f"  Bet {bet_id}: {with_id}/{total} legs with game_id ({pct}%) {status}")
    
    # Show remaining missing legs
    result = db.session.execute(db.text('''
        SELECT id, bet_id, player_name, game_date, away_team, home_team
        FROM bet_legs
        WHERE bet_id IN (158, 159, 160) AND game_id IS NULL
        ORDER BY bet_id, id
    '''))
    
    rows = result.fetchall()
    if rows:
        print("\nRemaining legs without game_ids:")
        for row in rows:
            print(f"  Leg {row[0]} (Bet {row[1]}): {row[2]}, {row[4]} vs {row[5]}, Date: {row[3]}")
        print("\n⚠ Note: These teams don't have games scheduled on their assigned dates:")
        print("  - Seahawks (appears on 11-16, not 11-24)")
        print("  - Jaguars (appears on 11-16, not 11-23)")
        print("  Consider verifying the correct game dates with the user.")
    else:
        print("\n✓ All legs have game_ids!")
    
    # Check betting_site status
    print("\nBetting site status:")
    result = db.session.execute(db.text('''
        SELECT id, betting_site FROM bets WHERE id IN (158, 159, 160) ORDER BY id
    '''))
    
    for row in result:
        status = "✓" if row[1] else "✗"
        print(f"  Bet {row[0]}: {status} betting_site = {row[1]}")
    
    print("\n" + "=" * 80)
