
from models import db


class Bet(db.Model):
    __tablename__ = 'bets'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    betting_site_id = db.Column(db.String(100))
    bet_type = db.Column(db.String(50))
    betting_site = db.Column(db.String(50))
    status = db.Column(db.String(20))
    is_active = db.Column(db.Boolean)
    is_archived = db.Column(db.Boolean)
    api_fetched = db.Column(db.String(3))
    bet_data = db.Column(db.Text)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    bet_date = db.Column(db.String(20))
    wager = db.Column(db.Numeric(10, 2))
    original_odds = db.Column(db.Integer)
    boosted_odds = db.Column(db.Integer)
    final_odds = db.Column(db.Integer)
    is_boosted = db.Column(db.Boolean)
    potential_winnings = db.Column(db.Numeric(10, 2))
    actual_winnings = db.Column(db.Numeric(10, 2))
    has_insurance = db.Column(db.Boolean)
    insurance_type = db.Column(db.String(50))
    insurance_amount = db.Column(db.Numeric(10, 2))
    insurance_triggered = db.Column(db.Boolean)
    total_legs = db.Column(db.Integer)
    legs_won = db.Column(db.Integer)
    legs_lost = db.Column(db.Integer)
    legs_pending = db.Column(db.Integer)
    legs_live = db.Column(db.Integer)
    legs_void = db.Column(db.Integer)
    last_api_update = db.Column(db.DateTime)
    secondary_bettors = db.Column(db.ARRAY(db.Integer))
    watchers = db.Column(db.ARRAY(db.Integer))
    bet_legs_rel = db.relationship('BetLeg', backref='bet', lazy=True)

    __mapper_args__ = {
        'include_properties': [
            'id', 'user_id', 'betting_site_id', 'bet_type', 'betting_site', 'status',
            'is_active', 'is_archived', 'api_fetched', 'bet_data', 'created_at', 'updated_at',
            'bet_date', 'wager', 'original_odds', 'boosted_odds', 'final_odds', 'is_boosted',
            'potential_winnings', 'actual_winnings', 'has_insurance', 'insurance_type',
            'insurance_amount', 'insurance_triggered', 'total_legs', 'legs_won', 'legs_lost',
            'legs_pending', 'legs_live', 'legs_void', 'last_api_update', 'secondary_bettors', 'watchers'
        ]
    }

    def get_bet_data(self):
        import json
        data = {}
        if self.bet_data:
            try:
                data = json.loads(self.bet_data)
            except Exception:
                data = {}
        
        # Include legs from database relationship if not already in bet_data
        if 'legs' not in data and self.bet_legs_rel:
            data['legs'] = [leg.to_dict() for leg in sorted(self.bet_legs_rel, key=lambda x: x.leg_order or 0)]
        
        return data

    def to_dict_structured(self, use_live_data=False):
        result = {
            'db_id': self.id,
            'betting_site_id': self.betting_site_id,
            'user_id': self.user_id,
            'bet_type': self.bet_type,
            'betting_site': self.betting_site,
            'status': self.status,
            'is_active': self.is_active,
            'is_archived': self.is_archived,
            'api_fetched': self.api_fetched,
            'bet_data': self.bet_data,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'bet_date': self.bet_date,
            'wager': float(self.wager) if self.wager is not None else None,
            'original_odds': self.original_odds,
            'boosted_odds': self.boosted_odds,
            'final_odds': self.final_odds,
            'is_boosted': self.is_boosted,
            'potential_winnings': float(self.potential_winnings) if self.potential_winnings is not None else None,
            'actual_winnings': float(self.actual_winnings) if self.actual_winnings is not None else None,
            'has_insurance': self.has_insurance,
            'insurance_type': self.insurance_type,
            'insurance_amount': float(self.insurance_amount) if self.insurance_amount is not None else None,
            'insurance_triggered': self.insurance_triggered,
            'total_legs': self.total_legs,
            'legs_won': self.legs_won,
            'legs_lost': self.legs_lost,
            'legs_pending': self.legs_pending,
            'legs_live': self.legs_live,
            'legs_void': self.legs_void,
            'last_api_update': self.last_api_update,
            'secondary_bettors': self.secondary_bettors,
            'watchers': self.watchers,
            # Add more fields as needed
        }
        
        # Include legs from database relationship
        if self.bet_legs_rel:
            result['legs'] = [leg.to_dict() for leg in sorted(self.bet_legs_rel, key=lambda x: x.leg_order or 0)]
        else:
            result['legs'] = []
            
        return result

    def to_dict(self):
        """Alias for to_dict_structured for backward compatibility"""
        return self.to_dict_structured()
