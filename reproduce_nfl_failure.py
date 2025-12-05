
from app import app, db, populate_game_ids_for_bet
from models import Bet, BetLeg
from datetime import datetime
import pytz

def reproduce_nfl_failure():
    with app.app_context():
        print("Creating test NFL bet...")
        
        # Create a test bet
        bet = Bet(user_id=1, betting_site='Test', bet_type='parlay', status='pending')
        db.session.add(bet)
        db.session.flush()
        
        eastern = pytz.timezone('US/Eastern')
        today = datetime.now(eastern).date()
        
        # Leg 1: Cowboys (Away) listed as Home
        leg1 = BetLeg(
            bet_id=bet.id,
            player_name='CeeDee Lamb',
            player_team='Dallas Cowboys',
            home_team='Dallas Cowboys', # Incorrectly listed as Home
            away_team='TBD',
            game_date=today,
            sport='NFL',
            bet_type='player_prop',
            target_value=0.0,
            status='pending'
        )
        db.session.add(leg1)
        
        # Leg 2: Lions (Home) listed as Home
        leg2 = BetLeg(
            bet_id=bet.id,
            player_name='Jared Goff',
            player_team='Detroit Lions',
            home_team='Detroit Lions', # Correctly listed as Home
            away_team='TBD',
            game_date=today,
            sport='NFL',
            bet_type='player_prop',
            target_value=0.0,
            status='pending'
        )
        db.session.add(leg2)
        
        db.session.commit()
        
        print(f"Created Bet {bet.id}")
        print(f"Leg 1: {leg1.player_team} (Home: {leg1.home_team})")
        print(f"Leg 2: {leg2.player_team} (Home: {leg2.home_team})")
        
        # Run population logic
        print("\nRunning populate_game_ids_for_bet...")
        try:
            populate_game_ids_for_bet(bet)
            db.session.commit()
        except Exception as e:
            print(f"Error: {e}")
            
        # Check result
        db.session.refresh(leg1)
        db.session.refresh(leg2)
        
        print(f"\nLeg 1 Final Game ID: {leg1.game_id}")
        print(f"Leg 1 Final Teams: {leg1.away_team} @ {leg1.home_team}")
        
        print(f"Leg 2 Final Game ID: {leg2.game_id}")
        print(f"Leg 2 Final Teams: {leg2.away_team} @ {leg2.home_team}")
        
        if leg1.game_id and leg2.game_id:
            print("✅ SUCCESS: Game IDs populated")
        else:
            print("❌ FAILURE: Game IDs NOT populated")
            
        # Cleanup
        print("\nCleaning up...")
        db.session.delete(leg1)
        db.session.delete(leg2)
        db.session.delete(bet)
        db.session.commit()

if __name__ == "__main__":
    reproduce_nfl_failure()
