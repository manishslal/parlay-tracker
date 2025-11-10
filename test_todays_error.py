"""
Test script to reproduce the 500 error when loading todays bets
"""
import sys
sys.path.insert(0, '/Users/manishslal/Desktop/Scrapper')

from app import app, db
from models import User, Bet, bet_users

with app.app_context():
    # Get JTahiliani user (case-insensitive)
    user = User.query.filter(User.username.ilike('jtahiliani')).first()
    
    if not user:
        print("❌ User JTahiliani not found")
        # Try listing all users
        all_users = User.query.all()
        print(f"Available users: {[u.username for u in all_users]}")
        sys.exit(1)
    
    print(f"✅ Found user: {user.username} (ID: {user.id})")
    
    # Query bets the same way the /todays endpoint does
    print("\n=== Querying bets (same as /todays endpoint) ===")
    query = Bet.query.join(bet_users, bet_users.c.bet_id == Bet.id).filter(
        bet_users.c.user_id == user.id,
        Bet.is_active == True,
        Bet.is_archived == False,
        Bet.status == 'pending'
    )
    
    bets = query.all()
    print(f"Found {len(bets)} pending bets")
    
    # Try to convert each bet to dict
    print("\n=== Converting bets to dict_structured ===")
    for i, bet in enumerate(bets, 1):
        print(f"\nBet {i}/{len(bets)}: ID={bet.id}, Type={bet.bet_type}")
        try:
            bet_dict = bet.to_dict_structured()
            print(f"  ✅ Success! Legs: {len(bet_dict.get('legs', []))}")
            print(f"  Name: {bet_dict.get('name')}")
            print(f"  Bettor: {bet_dict.get('bettor')}")
            
            # Check legs
            for j, leg in enumerate(bet_dict.get('legs', []), 1):
                print(f"    Leg {j}: {leg.get('player')} - {leg.get('stat')}")
                
        except Exception as e:
            print(f"  ❌ ERROR: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            print("\n" + "="*80)
            break
    
    print("\n" + "="*80)
    print("Test complete")
