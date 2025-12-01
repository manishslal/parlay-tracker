from app import app, db
from models import Bet, BetLeg

def inspect_bet():
    with app.app_context():
        bet_id_str = "DK638998623321891294"
        print(f"Searching for bet with bet_id: {bet_id_str}")
        
        target_bet = Bet.query.filter_by(betting_site_id=bet_id_str).first()
        
        if not target_bet:
            print("Bet not found by betting_site_id. Searching legs...")
            legs = BetLeg.query.filter(BetLeg.player_name.ilike("%Jahmyr Gibbs%")).all()
            for leg in legs:
                if leg.bet.betting_site_id == bet_id_str:
                    target_bet = leg.bet
                    break
        
        if not target_bet:
            print("Bet not found. Listing recent completed bets...")
            bets = Bet.query.filter_by(status='completed').order_by(Bet.created_at.desc()).limit(5).all()
            for b in bets:
                print(f"Bet DB ID: {b.id}, Site ID: {b.betting_site_id}, Status: {b.status}")
                target_bet = b # Just pick one to inspect if we can't find exact match
                break
        
        if target_bet:
            print(f"\nInspecting Bet DB ID: {target_bet.id}")
            print(f"Status: {target_bet.status}")
            print(f"Is Active: {target_bet.is_active}")
            
            # Inspect JSON data
            import json
            try:
                bet_data_json = json.loads(target_bet.bet_data)
                print("\nJSON Data Legs:")
                for i, leg in enumerate(bet_data_json.get('legs', [])):
                    print(f"Leg {i+1}: {leg.get('player')} - {leg.get('stat')}")
                    print(f"  Current (JSON): {leg.get('current')}")
                    print(f"  Final Value (JSON): {leg.get('final_value')}")
                    print(f"  Home Score (JSON): {leg.get('homeScore')}")
                    print(f"  Away Score (JSON): {leg.get('awayScore')}")
                    print(f"  Score Dict (JSON): {leg.get('score')}")
            except Exception as e:
                print(f"Error parsing bet_data: {e}")

            print("\nDB Columns:")
            legs = BetLeg.query.filter_by(bet_id=target_bet.id).order_by(BetLeg.leg_order).all()
            for i, leg in enumerate(legs):
                print(f"Leg {i+1}: {leg.player_name} - {leg.stat_type}")
                print(f"  Achieved Value (DB): {leg.achieved_value}")
                print(f"  Home Score (DB): {leg.home_score}")
                print(f"  Away Score (DB): {leg.away_score}")

if __name__ == "__main__":
    inspect_bet()
