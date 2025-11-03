#!/usr/bin/env python3
"""
Fix Duplicate Sam Darnold Leg in 7-Leg SGP
==========================================
Removes the duplicate "Sam Darnold 200+ passing yards" leg
from bet ID O/0240915/0000066
"""

import os
import psycopg2
import json

def fix_duplicate_leg():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not set")
        return
    
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    print("\n" + "="*70)
    print("FIX DUPLICATE SAM DARNOLD LEG")
    print("="*70)
    
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Find the bet by bet_id
        cur.execute("""
            SELECT id, bet_data
            FROM bets
            WHERE bet_id = %s
        """, ('O/0240915/0000066',))
        
        result = cur.fetchone()
        if not result:
            print("❌ Bet O/0240915/0000066 not found!")
            return
        
        db_bet_id, bet_data = result
        bet_data = json.loads(bet_data)
        
        print(f"\n✅ Found bet (DB ID: {db_bet_id})")
        print(f"Current legs: {len(bet_data['legs'])}")
        
        # Show current legs
        print("\nCurrent legs:")
        for i, leg in enumerate(bet_data['legs'], 1):
            stat_display = leg['stat'].replace('_', ' ').title()
            addon = f" ({leg['stat_add']})" if leg.get('stat_add') else ""
            print(f"  {i}. {leg['player']} - {stat_display} {leg['target']}{addon}")
        
        # Remove the duplicate Sam Darnold leg (the second one at index 1)
        original_count = len(bet_data['legs'])
        
        # Find and remove duplicate Sam Darnold entries
        # Keep only the first one
        seen_legs = []
        unique_legs = []
        
        for leg in bet_data['legs']:
            leg_key = (leg['player'], leg['stat'], leg['target'], leg.get('stat_add'))
            if leg_key not in seen_legs:
                seen_legs.append(leg_key)
                unique_legs.append(leg)
            else:
                print(f"\n🗑️  Removing duplicate: {leg['player']} - {leg['stat']} {leg['target']} {leg.get('stat_add', '')}")
        
        bet_data['legs'] = unique_legs
        
        print(f"\nLegs after removing duplicates: {len(bet_data['legs'])}")
        print("\nUpdated legs:")
        for i, leg in enumerate(bet_data['legs'], 1):
            stat_display = leg['stat'].replace('_', ' ').title()
            addon = f" ({leg['stat_add']})" if leg.get('stat_add') else ""
            print(f"  {i}. {leg['player']} - {stat_display} {leg['target']}{addon}")
        
        # Update the bet_data in database
        cur.execute("""
            UPDATE bets
            SET bet_data = %s,
                updated_at = NOW()
            WHERE id = %s
        """, (json.dumps(bet_data), db_bet_id))
        
        conn.commit()
        
        print(f"\n✅ Updated bet {db_bet_id}")
        print(f"Removed {original_count - len(bet_data['legs'])} duplicate leg(s)")
        print("\nThe bet should now show as a 7-leg parlay (not 8)")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    fix_duplicate_leg()
