
from app import app, db, populate_game_ids_for_bet
from models import Bet, BetLeg
from sqlalchemy import or_

def force_populate():
    with app.app_context():
        print("Force populating game IDs...")
        
        # Find bets with missing game IDs
        legs = BetLeg.query.filter(
            or_(BetLeg.game_id.is_(None), BetLeg.game_id == ''),
            BetLeg.status.in_(['pending', 'live']),
            BetLeg.game_date.isnot(None)
        ).all()
        
        if not legs:
            print("No legs found needing population.")
            return
            
        # Get unique bet IDs
        bet_ids = set(leg.bet_id for leg in legs)
        print(f"Found {len(legs)} legs across {len(bet_ids)} bets.")
        
        for bet_id in bet_ids:
            print(f"\nProcessing Bet {bet_id}...")
            try:
                bet = Bet.query.get(bet_id)
                if bet:
                    populate_game_ids_for_bet(bet)
                    db.session.commit()
                    print(f"✅ Successfully populated Bet {bet_id}")
                else:
                    print(f"❌ Bet {bet_id} not found")
            except Exception as e:
                print(f"❌ Error processing Bet {bet_id}: {e}")
                db.session.rollback()

if __name__ == "__main__":
    force_populate()
