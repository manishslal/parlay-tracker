
from app import app, db
from models import Bet, BetLeg, User
from datetime import datetime

def create_test_bet():
    with app.app_context():
        # Ensure user exists
        user = User.query.get(1)
        if not user:
            print("Creating test user...")
            user = User(id=1, username="testuser", email="test@example.com")
            db.session.add(user)
            db.session.commit()

        # Create a test bet
        print("Creating test bet...")
        bet = Bet(
            user_id=1,
            betting_site='DraftKings',
            wager=10.0,
            final_odds=100,
            status='pending',
            is_active=True
        )
        db.session.add(bet)
        db.session.commit()
        
        # Create a test leg (Over bet that has hit)
        print(f"Creating test leg for Bet {bet.id}...")
        leg = BetLeg(
            bet_id=bet.id,
            player_name="Test Player",
            home_team="Team A",
            away_team="Team B",
            bet_type="player_prop",
            stat_type="points",
            bet_line_type="over",
            target_value=20.0,
            achieved_value=25.0, # Already hit!
            status="pending",
            is_hit=None, # Unknown status
            game_status="STATUS_IN_PROGRESS" # Still live
        )
        db.session.add(leg)
        db.session.commit()
        
        print(f"Created Bet {bet.id} with Leg {leg.id}")
        print(f"Leg Status: {leg.status}, Is Hit: {leg.is_hit}, Achieved: {leg.achieved_value}, Target: {leg.target_value}")

if __name__ == "__main__":
    create_test_bet()
