from app import app
from models import Bet, BetLeg

def debug_bet_status():
    print("Debugging bet status...")
    with app.app_context():
        bet = Bet.query.get(6)
        if not bet:
            print("Bet 6 not found")
            return
            
        print(f"Bet: {bet.bet_type} (ID: {bet.id})")
        for leg in bet.bet_legs_rel:
            if "Mitchell" in leg.player_name:
                print(f"Leg: {leg.player_name} - {leg.stat_type}")
                print(f"  Status: {leg.status}")
                print(f"  Is Hit: {leg.is_hit}")
                print(f"  Achieved Value: {leg.achieved_value}")
                print(f"  Target Value: {leg.target_value}")
                print(f"  Game Date: {leg.game_date}")
                print(f"  Game Status: {leg.game_status}")

if __name__ == "__main__":
    debug_bet_status()
