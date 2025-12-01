from app import app, db
from models import User, Bet, BetLeg

def debug_bet_legs():
    print("Debugging Bet Legs...")
    
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        if not user:
            print("User 'testuser' not found.")
            return

        print(f"User ID: {user.id}")
        
        # Get recent bets
        bets = Bet.query.filter_by(user_id=user.id).order_by(Bet.created_at.desc()).limit(5).all()
        print(f"Found {len(bets)} bets.")
        
        for bet in bets:
            print(f"\n--- Bet ID: {bet.id} ---")
            print(f"Description: {bet.betting_site} - {bet.wager}")
            
            # 1. Direct Query for BetLegs
            legs_query = BetLeg.query.filter_by(bet_id=bet.id).all()
            print(f"Direct BetLeg Query Count: {len(legs_query)}")
            for leg in legs_query:
                print(f"  - Leg ID: {leg.id}, Player: {leg.player_name}, Team: {leg.player_team}, Status: {leg.status}")
            
            # 2. Relationship Access
            print(f"Relationship (bet.bet_legs_rel) Count: {len(bet.bet_legs_rel)}")
            
            # 3. Serialization
            bet_dict = bet.to_dict_structured()
            serialized_legs = bet_dict.get('legs', [])
            print(f"Serialized 'legs' Count: {len(serialized_legs)}")
            if not serialized_legs:
                print("  WARNING: Serialized legs are empty!")

if __name__ == "__main__":
    debug_bet_legs()
