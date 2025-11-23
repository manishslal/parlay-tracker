#!/usr/bin/env python3
"""
Final fix for the last 3 legs:
- Leg 922 (Bet 159): Seahawks on 11-24 → Seahawks @ Titans on 11-23 (ID: 401772886)
- Leg 926 (Bet 160): Seahawks on 11-24 → Seahawks @ Titans on 11-23 (ID: 401772886)
- Leg 928 (Bet 160): Jaguars on 11-23 → Jaguars @ Cardinals on 11-23 (ID: 401772783)
"""

from app import app, db
from datetime import datetime

with app.app_context():
    print("=" * 80)
    print("FINAL FIX: Updating last 3 Seahawks and Jaguars legs")
    print("=" * 80)
    
    # 1. Update both Seahawks legs (922, 926) with Seahawks @ Titans game
    print("\n1. Updating Seahawks legs (922, 926)...")
    print("   Game: Seattle Seahawks @ Tennessee Titans, 2025-11-23, ID: 401772886")
    db.session.execute(db.text('''
        UPDATE bet_legs 
        SET game_id = 401772886,
            home_team = 'Tennessee Titans',
            away_team = 'Seattle Seahawks',
            game_date = '2025-11-23'
        WHERE id IN (922, 926)
    '''))
    print("   ✓ Updated legs 922 and 926")
    
    # 2. Update Jaguars leg (928) with Jaguars @ Cardinals game
    print("\n2. Updating Jaguars leg (928)...")
    print("   Game: Jacksonville Jaguars @ Arizona Cardinals, 2025-11-23, ID: 401772783")
    db.session.execute(db.text('''
        UPDATE bet_legs 
        SET game_id = 401772783,
            home_team = 'Arizona Cardinals',
            away_team = 'Jacksonville Jaguars'
        WHERE id = 928
    '''))
    print("   ✓ Updated leg 928")
    
    # Commit changes
    db.session.commit()
    print("\n✓ All changes committed to database")
    
    # Display final status
    print("\n" + "=" * 80)
    print("FINAL STATUS - ALL BETS")
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
    all_complete = True
    for row in result:
        bet_id, total, with_id, missing = row
        pct = int((with_id / total) * 100)
        if missing == 0:
            status = "✓ COMPLETE"
        else:
            status = "⚠ INCOMPLETE"
            all_complete = False
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
        print("\n❌ Remaining legs without game_ids:")
        for row in rows:
            print(f"  Leg {row[0]} (Bet {row[1]}): {row[2]}, {row[4]} vs {row[5]}, Date: {row[3]}")
    else:
        print("\n✅ ALL LEGS NOW HAVE GAME_IDS!")
    
    # Final details
    print("\n" + "=" * 80)
    print("DETAILS")
    print("=" * 80)
    
    result = db.session.execute(db.text('''
        SELECT bl.id, bl.bet_id, bl.player_name, bl.away_team, bl.home_team, bl.game_date, bl.game_id
        FROM bet_legs bl
        WHERE bl.bet_id IN (158, 159, 160)
        ORDER BY bl.bet_id, bl.id
    '''))
    
    current_bet = None
    for row in result:
        if row[1] != current_bet:
            if current_bet is not None:
                print()
            current_bet = row[1]
            print(f"Bet {current_bet}:")
        
        leg_id, bet_id, player, away, home, date, game_id = row
        status = "✓" if game_id else "✗"
        print(f"  {status} Leg {leg_id}: {player} - {away} @ {home} ({date})")
    
    print("\n" + "=" * 80)
    
    if all_complete:
        print("🎉 SUCCESS! All bets are now fully populated with game_ids!")
    else:
        print("⚠ Some bets still have missing game_ids")
