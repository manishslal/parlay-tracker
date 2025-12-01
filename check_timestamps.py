from app import app, db
from models import Bet, BetLeg
from sqlalchemy import or_

with app.app_context():
    # Find bets with Celtics legs
    legs = BetLeg.query.filter(or_(BetLeg.player_name.ilike('%Celtics%'), BetLeg.player_team.ilike('%Celtics%'))).all()
    print(f"Found {len(legs)} Celtics legs.")
    for leg in legs:
        bet = Bet.query.get(leg.bet_id)
        print(f"Bet {bet.id} created at: {bet.created_at}")
