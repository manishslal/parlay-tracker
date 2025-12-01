from app import app, db
from models import Bet, BetLeg
import json

with app.app_context():
    bets = Bet.query.all()
    print(f"Found {len(bets)} bets in the database.")
    for bet in bets:
        print(f"Bet ID: {bet.id}, User ID: {bet.user_id}, Status: {bet.status}")
        legs = BetLeg.query.filter_by(bet_id=bet.id).all()
        for leg in legs:
            print(f"  - Leg: {leg.player_name} ({leg.player_team}) - {leg.bet_type} {leg.target_value}")
