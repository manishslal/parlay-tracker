
from app import app, db, populate_game_ids_for_bet
from models import Bet, BetLeg
from datetime import datetime
import pytz

def reproduce_issue():
    with app.app_context():
        print("Creating test bet...")
        
        # Create a test bet
        bet = Bet(user_id=1, betting_site='Test', bet_type='parlay', status='pending')
        db.session.add(bet)
        db.session.flush()
        
        # Create a leg that should match Lakers vs Raptors
        # Using "Lakers" as team name to test normalization
        eastern = pytz.timezone('US/Eastern')
        today = datetime.now(eastern).date()
        
        leg = BetLeg(
            bet_id=bet.id,
            player_name='LeBron James',
            player_team='Lakers', # Should normalize to Los Angeles Lakers
            home_team='Lakers',   # Should normalize
            away_team='Raptors',  # Should normalize
            game_date=today,
            sport='NBA',
            bet_type='player_prop',
            target_value=0.0,
            status='pending'
        )
        db.session.add(leg)
        db.session.commit()
        
        print(f"Created Bet {bet.id} with Leg {leg.id}")
        print(f"Initial Game ID: {leg.game_id}")
        print(f"Initial Teams: {leg.away_team} @ {leg.home_team}")
        
        # Run population logic
        print("\nRunning populate_game_ids_for_bet...")
        try:
            populate_game_ids_for_bet(bet)
            db.session.commit()
        except Exception as e:
            print(f"Error: {e}")
            
        # Check result
        db.session.refresh(leg)
        print(f"\nFinal Game ID: {leg.game_id}")
        print(f"Final Teams: {leg.away_team} @ {leg.home_team}")
        
        if leg.game_id:
            print("✅ SUCCESS: Game ID populated")
        else:
            print("❌ FAILURE: Game ID NOT populated")
            
        # Cleanup
        print("\nCleaning up...")
        db.session.delete(leg)
        db.session.delete(bet)
        db.session.commit()

if __name__ == "__main__":
    reproduce_issue()
