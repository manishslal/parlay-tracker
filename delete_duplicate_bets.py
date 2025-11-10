#!/usr/bin/env python3
"""
Delete duplicate bets (106, 107) which are duplicates of (108, 109)
Uses SQLAlchemy's cascade delete to automatically remove associated bet_legs
"""

from app import app, db, Bet, BetLeg

def delete_bets(bet_ids):
    """
    Delete bets by their database IDs
    
    Args:
        bet_ids: List of bet.id values to delete
    
    Returns:
        Tuple of (deleted_bets_count, deleted_legs_count)
    """
    with app.app_context():
        deleted_bets = 0
        deleted_legs = 0
        
        for bet_id in bet_ids:
            # Find the bet
            bet = Bet.query.get(bet_id)
            
            if not bet:
                print(f"⚠️  Bet ID {bet_id} not found")
                continue
            
            # Get info before deleting
            bet_data = bet.get_bet_data()
            bet_name = bet_data.get('name', 'Unknown')
            bet_identifier = bet_data.get('bet_id', 'Unknown')
            leg_count = bet.bet_legs_rel.count()
            
            print(f"\n🗑️  Deleting Bet {bet_id}:")
            print(f"   Name: {bet_name}")
            print(f"   Bet ID: {bet_identifier}")
            print(f"   User ID: {bet.user_id}")
            print(f"   Legs: {leg_count}")
            
            # Delete the bet (cascade will automatically delete bet_legs)
            db.session.delete(bet)
            deleted_bets += 1
            deleted_legs += leg_count
        
        # Commit all deletions
        db.session.commit()
        
        print(f"\n✅ Deleted {deleted_bets} bets and {deleted_legs} legs")
        return deleted_bets, deleted_legs


def delete_by_bet_identifier(bet_identifiers):
    """
    Delete bets by their bet_id field (e.g., "O/0240915/0000068")
    
    Args:
        bet_identifiers: List of bet_id strings to delete
    
    Returns:
        Tuple of (deleted_bets_count, deleted_legs_count)
    """
    with app.app_context():
        deleted_bets = 0
        deleted_legs = 0
        
        for identifier in bet_identifiers:
            # Find all bets with this identifier
            bets = Bet.query.filter_by(bet_id=identifier).all()
            
            if not bets:
                print(f"⚠️  No bets found with bet_id: {identifier}")
                continue
            
            for bet in bets:
                bet_data = bet.get_bet_data()
                bet_name = bet_data.get('name', 'Unknown')
                leg_count = bet.bet_legs_rel.count()
                
                print(f"\n🗑️  Deleting Bet {bet.id}:")
                print(f"   Name: {bet_name}")
                print(f"   Bet ID: {identifier}")
                print(f"   User ID: {bet.user_id}")
                print(f"   Legs: {leg_count}")
                
                db.session.delete(bet)
                deleted_bets += 1
                deleted_legs += leg_count
        
        # Commit all deletions
        db.session.commit()
        
        print(f"\n✅ Deleted {deleted_bets} bets and {deleted_legs} legs")
        return deleted_bets, deleted_legs


if __name__ == '__main__':
    print("=" * 60)
    print("Delete Duplicate Bets (106, 107)")
    print("=" * 60)
    
    # Method 1: Delete by database ID
    # These are the duplicate bets (106, 107) that are copies of (108, 109)
    duplicate_bet_ids = [106, 107]
    
    # Confirm before deletion
    print("\n⚠️  WARNING: This will permanently delete the following bets:")
    
    with app.app_context():
        for bet_id in duplicate_bet_ids:
            bet = Bet.query.get(bet_id)
            if bet:
                bet_data = bet.get_bet_data()
                print(f"   - Bet {bet_id}: {bet_data.get('name', 'Unknown')} ({bet.bet_legs_rel.count()} legs)")
    
    response = input("\nType 'DELETE' to confirm: ")
    
    if response == 'DELETE':
        delete_bets(duplicate_bet_ids)
        print("\n✅ Deletion complete!")
    else:
        print("\n❌ Deletion cancelled")
