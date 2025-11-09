#!/usr/bin/env python3
"""
Update bet_legs status based on achieved_value vs target_value
For historical bets that have achieved_value but status is still 'pending'
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor

def update_bet_legs_status():
    """Update bet_legs status for completed bets"""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        return
    
    # Fix Render's postgres:// to postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    
    try:
        # Get all legs that need status update
        cursor.execute('''
            SELECT bl.id, bl.player_name, bl.bet_type, bl.bet_line_type, 
                   bl.target_value, bl.achieved_value
            FROM bet_legs bl
            JOIN bets b ON bl.bet_id = b.id
            WHERE b.is_active = FALSE
              AND bl.achieved_value IS NOT NULL
              AND bl.status = 'pending'
        ''')
        
        legs_to_update = cursor.fetchall()
        print(f"Found {len(legs_to_update)} legs to update")
        print("=" * 80)
        
        won_count = 0
        lost_count = 0
        
        for leg in legs_to_update:
            # Determine if leg was won or lost
            # For "over" bets: achieved >= target = won
            # For "under" bets: achieved <= target = won
            # Default to "over" logic for now (most common)
            bet_line_type = leg['bet_line_type'] or 'over'
            target = float(leg['target_value'])
            achieved = float(leg['achieved_value'])
            
            if bet_line_type == 'under':
                is_won = achieved <= target
            else:  # 'over' or None
                is_won = achieved >= target
            
            new_status = 'won' if is_won else 'lost'
            is_hit = True if is_won else False
            
            # Update the leg
            cursor.execute('''
                UPDATE bet_legs
                SET status = %s, is_hit = %s
                WHERE id = %s
            ''', (new_status, is_hit, leg['id']))
            
            if is_won:
                won_count += 1
                symbol = "✅"
            else:
                lost_count += 1
                symbol = "❌"
            
            if len(legs_to_update) <= 20:  # Show details for small batches
                print(f"{symbol} {leg['player_name']}: {leg['bet_type']} {bet_line_type}")
                print(f"   Target: {target}, Achieved: {achieved} → {new_status.upper()}")
        
        conn.commit()
        
        print("\n" + "=" * 80)
        print(f"✅ Updated {len(legs_to_update)} bet legs:")
        print(f"   Won: {won_count}")
        print(f"   Lost: {lost_count}")
        print("=" * 80)
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    update_bet_legs_status()
