from app import app
from models import User
from services.user_service import get_user_bets_query
from services.bet_service import process_parlay_data

def verify_live_stats():
    print("Verifying live stats...")
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        if not user:
            print("User not found")
            return
            
        # Get live bets
        query = get_user_bets_query(user, status=['live', 'pending'])
        bets = query.all()
        
        # Convert to dicts
        bet_dicts = [b.to_dict_structured() for b in bets]
        
        # Process with live data
        processed_bets = process_parlay_data(bet_dicts)
        
        for bet in processed_bets:
            print(f"\nBet: {bet.get('name')} (ID: {bet.get('db_id')})")
            for leg in bet.get('legs', []):
                player = leg.get('player')
                stat = leg.get('stat')
                current = leg.get('current')
                target = leg.get('target')
                bet_score = leg.get('bet_team_score')
                opp_score = leg.get('opponent_score')
                print(f"  - {player} {stat}: Current={current} (Target={target}) [Score: {bet_score}-{opp_score}]")

if __name__ == "__main__":
    verify_live_stats()
