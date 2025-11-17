
from models import db

class BetLeg(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bet_id = db.Column(db.Integer, db.ForeignKey('bet.id'))
    # Add more fields and methods as needed
