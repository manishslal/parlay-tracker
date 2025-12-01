from app import app
from models import Bet, BetLeg

def check_garland_leg_data():
    print("=== Garland Leg Data ===\n")
    with app.app_context():
        bet = Bet.query.get(8)
        if not bet:
            print("Bet 8 not found")
            return
        
        for leg in bet.bet_legs_rel:
            if "Garland" in leg.player_name:
                print(f"Player: {leg.player_name}")
                print(f"Stat: {leg.stat_type}")
                print(f"Home Team: '{leg.home_team}'")
                print(f"Away Team: '{leg.away_team}'")
                print(f"Game Date: {leg.game_date}")
                print(f"Sport: {leg.sport}")
                print(f"Target: {leg.target_value}")
                print(f"Achieved: {leg.achieved_value}")
                print(f"Game Status: {leg.game_status}")
                
                # Convert to dict to see what process_parlay_data receives
                leg_dict = leg.to_dict()
                print(f"\nAs dict:")
                print(f"  home: '{leg_dict.get('home')}'")
                print(f"  away: '{leg_dict.get('away')}'")
                print(f"  game_date: '{leg_dict.get('game_date')}'")
                print(f"  sport: '{leg_dict.get('sport')}'")

if __name__ == "__main__":
    check_garland_leg_data()
