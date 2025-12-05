
from app import app, db
from models import Bet, BetLeg
from sqlalchemy import or_

def find_failed_bets():
    with app.app_context():
        print("Searching for bets with missing Game IDs...")
        
        legs = BetLeg.query.filter(
            or_(BetLeg.game_id.is_(None), BetLeg.game_id == ''),
            BetLeg.status.in_(['pending', 'live']),
            BetLeg.game_date.isnot(None)
        ).order_by(BetLeg.created_at.desc()).limit(20).all()
        
        if not legs:
            print("No problematic legs found.")
            return
            
        print(f"Found {len(legs)} legs with missing Game IDs:")
        for leg in legs:
            print(f"\n--- Leg ID: {leg.id} (Bet ID: {leg.bet_id}) ---")
            print(f"  Player: {leg.player_name}")
            print(f"  Team: {leg.player_team}")
            print(f"  Matchup: {leg.away_team} @ {leg.home_team}")
            print(f"  Game ID: {repr(leg.game_id)}")
            print(f"  Date: {leg.game_date}")
            print(f"  Sport: {leg.sport}")
            print(f"  Created: {leg.created_at}")

if __name__ == "__main__":
    find_failed_bets()
