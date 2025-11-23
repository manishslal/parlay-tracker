#!/usr/bin/env python3
"""
Move bet 153 back to live status since it was incorrectly moved to historical.

The issue was that the bet had legs with game_status='unknown', which the 
auto_move_bets_no_live_legs() function incorrectly treated as "no live games".
"""

from app import app, db

with app.app_context():
    print("=" * 80)
    print("FIXING BET 153 - MOVING BACK TO LIVE STATUS")
    print("=" * 80)
    
    # Get bet 153
    result = db.session.execute(db.text('''
        SELECT id, status, is_active FROM bets WHERE id = 153
    '''))
    
    bet = result.fetchone()
    if not bet:
        print("❌ Bet 153 not found")
    else:
        print(f"\nBet 153 Current Status:")
        print(f"  ID: {bet[0]}")
        print(f"  Status: {bet[1]}")
        print(f"  Is Active: {bet[2]}")
        
        # Update the bet status
        print(f"\nUpdating Bet 153:")
        db.session.execute(db.text('''
            UPDATE bets SET status = 'live', is_active = TRUE WHERE id = 153
        '''))
        
        db.session.commit()
        print(f"  ✓ Status: completed → live")
        print(f"  ✓ Is Active: FALSE → TRUE")
        
        # Verify the fix
        result = db.session.execute(db.text('''
            SELECT id, status, is_active FROM bets WHERE id = 153
        '''))
        
        bet_after = result.fetchone()
        print(f"\nBet 153 New Status:")
        print(f"  ID: {bet_after[0]}")
        print(f"  Status: {bet_after[1]}")
        print(f"  Is Active: {bet_after[2]}")
        
        if bet_after[1] == 'live' and bet_after[2]:
            print("\n✅ Bet 153 has been successfully moved back to live!")
        else:
            print("\n❌ Something went wrong with the update")
    
    # Show the legs
    print("\n" + "=" * 80)
    print("BET 153 LEGS:")
    print("=" * 80)
    result = db.session.execute(db.text('''
        SELECT id, player_name, stat_type, game_status, status FROM bet_legs WHERE bet_id = 153 ORDER BY id
    '''))
    
    for row in result:
        print(f"  Leg {row[0]}: {row[1]}, {row[2]}, game_status={row[3]}, leg_status={row[4]}")
