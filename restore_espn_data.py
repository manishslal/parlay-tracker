#!/usr/bin/env python3
"""
Restore ESPN game data from local Historical_Bets.json backup to PostgreSQL
This preserves the 'current' values and game results that were previously fetched
"""
import json
import sys
from app import app, db
from models import Bet

def restore_espn_data(backup_file):
    """Restore ESPN data from backup JSON to PostgreSQL bets"""
    
    print("Loading backup data...")
    with open(backup_file, 'r') as f:
        backup_data = json.load(f)
    
    if not backup_data:
        print("❌ Backup file is empty! Check the file path.")
        return
    
    print(f"✅ Loaded {len(backup_data)} bets from backup\n")
    
    with app.app_context():
        # Get all completed bets from database
        completed_bets = Bet.query.filter_by(status='completed').all()
        print(f"📊 Found {len(completed_bets)} completed bets in PostgreSQL")
        
        updated_count = 0
        skipped_count = 0
        already_have_data = 0
        
        for db_bet in completed_bets:
            bet_data = db_bet.get_bet_data()
            bet_name = bet_data.get('name', '')
            
            # Find matching bet in backup by name
            backup_bet = None
            for b in backup_data:
                if b.get('name') == bet_name:
                    backup_bet = b
                    break
            
            if not backup_bet:
                print(f"  ⏭️  No backup found for: {bet_name}")
                skipped_count += 1
                continue
            
            # Check if this bet already has ESPN data
            has_espn_data = False
            for leg in bet_data.get('legs', []):
                if 'current' in leg and leg.get('current') is not None:
                    has_espn_data = True
                    break
            
            if has_espn_data:
                already_have_data += 1
                continue  # Skip bets that already have data
            
            # Merge ESPN data from backup into database bet
            # Preserve the leg structure but add ESPN results
            for i, leg in enumerate(bet_data.get('legs', [])):
                if i < len(backup_bet.get('legs', [])):
                    backup_leg = backup_bet['legs'][i]
                    
                    # Copy ESPN data fields
                    if 'current' in backup_leg:
                        leg['current'] = backup_leg['current']
                    if 'score' in backup_leg:
                        leg['score'] = backup_leg['score']
                    if 'score_diff' in backup_leg:
                        leg['score_diff'] = backup_leg['score_diff']
                    if 'status' in backup_leg:
                        leg['status'] = backup_leg['status']
                    if 'final_value' in backup_leg:
                        leg['final_value'] = backup_leg['final_value']
                    if 'result' in backup_leg:
                        leg['result'] = backup_leg['result']
                    if 'game_status' in backup_leg:
                        leg['game_status'] = backup_leg['game_status']
            
            # Copy games array if it exists
            if 'games' in backup_bet:
                bet_data['games'] = backup_bet['games']
            
            # Save updated bet data back to database
            db_bet.set_bet_data(bet_data, preserve_status=True)
            db_bet.api_fetched = 'Yes'  # Mark as fetched
            
            updated_count += 1
            print(f"  ✅ Restored ESPN data for: {bet_name}")
        
        # Commit all changes
        db.session.commit()
        
        print(f"\n✅ Restore complete!")
        print(f"  ✅ Updated: {updated_count} bets")
        print(f"  ⏭️  Skipped: {skipped_count} bets")
        print(f"\n📊 Final stats:")
        print(f"  Total completed bets: {Bet.query.filter_by(status='completed').count()}")
        print(f"  Bets with ESPN data: {updated_count}")
        
        return True

if __name__ == '__main__':
    # Use the latest backup folder that has the full data (107KB)
    backup_file = 'data/backup_20251101_110041/Historical_Bets.json'
    
    print("� Starting ESPN Data Restoration")
    print(f"� Using backup file: {backup_file}\n")
    
    restore_espn_data(backup_file)
