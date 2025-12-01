
from app import app, db
from models import Bet, BetLeg

def debug_bet_leg():
    with app.app_context():
        # Search for leg 1049 directly
        leg = BetLeg.query.get(1049)
        if leg:
            print(f"FOUND Leg 1049! It belongs to Bet ID: {leg.bet_id}")
            print(f"Player: {leg.player_name}")
            print(f"Stat Type: {leg.stat_type}")
            print(f"Bet Line Type: {leg.bet_line_type}")
            print(f"Target Value: {leg.target_value}")
            print(f"Achieved Value: {leg.achieved_value}")
            print(f"Status: {leg.status}")
            print(f"Is Hit: {leg.is_hit}")
            print(f"Game Status: {leg.game_status}")
        else:
            print("Leg 1049 NOT found in database!")
            
            # Count total bets and legs
            bet_count = Bet.query.count()
            leg_count = BetLeg.query.count()
            print(f"Total Bets in DB: {bet_count}")
            print(f"Total Legs in DB: {leg_count}")

if __name__ == "__main__":
    debug_bet_leg()
