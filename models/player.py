from models import db
from datetime import datetime

class Player(db.Model):
    """Player model for storing player information"""
    __tablename__ = 'players'

    id = db.Column(db.Integer, primary_key=True)
    player_name = db.Column(db.String(100), nullable=False)
    normalized_name = db.Column(db.String(100), nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    sport = db.Column(db.String(50), nullable=False)
    position = db.Column(db.String(20))
    position_group = db.Column(db.String(20))
    jersey_number = db.Column(db.Integer)
    current_team = db.Column(db.String(50))
    team_abbreviation = db.Column(db.String(10))
    previous_teams = db.Column(db.Text)
    espn_player_id = db.Column(db.String(50))
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to bet legs
    bet_legs = db.relationship('BetLeg', backref='player', lazy='dynamic')

    def __repr__(self):
        return f'<Player {self.player_name} ({self.sport})>'