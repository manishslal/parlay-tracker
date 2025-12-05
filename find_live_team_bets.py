
from app import app, db
from models import BetLeg
from sqlalchemy import or_

def find_live_bets():
    with app.app_context():
        print("Searching for bets with 'Live' team name...")
        
        legs = BetLeg.query.filter(
            or_(BetLeg.home_team.ilike('%Live%'), BetLeg.away_team.ilike('%Live%')),
            BetLeg.game_date.isnot(None)
        ).all()
        
        if not legs:
            print("No 'Live' team bets found.")
            return
            
        print(f"Found {len(legs)} legs:")
        for leg in legs:
            print(f"\n--- Leg ID: {leg.id} (Bet ID: {leg.bet_id}) ---")
            print(f"  Player: {leg.player_name}")
            print(f"  Player Team: {leg.player_team}")
            print(f"  Matchup: {leg.away_team} @ {leg.home_team}")
            print(f"  Game ID: {repr(leg.game_id)}")
            print(f"  Date: {leg.game_date}")
            print(f"  Status: {leg.status}")

if __name__ == "__main__":
    find_live_bets()
