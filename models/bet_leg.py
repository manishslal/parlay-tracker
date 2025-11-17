
from models import db

class BetLeg(db.Model):
    __tablename__ = 'bet_legs'  # Use the correct table name
    
    id = db.Column(db.Integer, primary_key=True)
    bet_id = db.Column(db.Integer, db.ForeignKey('bets.id'))
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'))

    # Player/Team Info (Denormalized for performance)
    player_name = db.Column(db.String(100), nullable=False)
    player_team = db.Column(db.String(50))
    player_position = db.Column(db.String(10))

    # Game Info
    home_team = db.Column(db.String(50), nullable=False)
    away_team = db.Column(db.String(50), nullable=False)
    game_id = db.Column(db.String(50))
    game_date = db.Column(db.Date)
    game_time = db.Column(db.Time)
    game_status = db.Column(db.String(20))
    sport = db.Column(db.String(50))
    parlay_sport = db.Column(db.String(50))

    # Bet Details
    bet_type = db.Column(db.String(50), nullable=False)
    stat_type = db.Column(db.String(50))  # Moved here, increased size
    bet_line_type = db.Column(db.String(20))  # 'over', 'under', NULL
    target_value = db.Column(db.Numeric(10, 2), nullable=False)
    achieved_value = db.Column(db.Numeric(10, 2))

    # Performance Comparison
    player_season_avg = db.Column(db.Numeric(10, 2))
    player_last_5_avg = db.Column(db.Numeric(10, 2))
    vs_opponent_avg = db.Column(db.Numeric(10, 2))
    target_vs_season = db.Column(db.Numeric(10, 2))

    # Odds Tracking
    original_leg_odds = db.Column(db.Integer)
    boosted_leg_odds = db.Column(db.Integer)
    final_leg_odds = db.Column(db.Integer)

    # Leg Status
    status = db.Column(db.String(20), default='pending')
    is_hit = db.Column(db.Boolean)
    void_reason = db.Column(db.String(100))

    # Live Game Data
    current_quarter = db.Column(db.String(10))
    time_remaining = db.Column(db.String(20))
    home_score = db.Column(db.Integer)
    away_score = db.Column(db.Integer)

    # Contextual Data
    is_home_game = db.Column(db.Boolean)
    weather_conditions = db.Column(db.String(100))
    injury_during_game = db.Column(db.Boolean, default=False)
    dnp_reason = db.Column(db.String(100))

    # Metadata
    leg_order = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'bet_id': self.bet_id,
            'player_id': self.player_id,
            'player': self.player_name,  # Frontend expects 'player'
            'player_name': self.player_name,
            'player_team': self.player_team,
            'team': self.player_team,  # Frontend expects 'team'
            'player_position': self.player_position,
            'position': self.player_position,  # Frontend expects 'position'
            'home': self.home_team,  # Frontend expects 'home'
            'home_team': self.home_team,
            'away': self.away_team,  # Frontend expects 'away'
            'away_team': self.away_team,
            'game_id': self.game_id,
            'game_date': self.game_date.isoformat() if self.game_date else None,
            'game_time': self.game_time.isoformat() if self.game_time else None,
            'gameStatus': self.game_status,  # Frontend expects 'gameStatus'
            'score_diff': (self.home_score - self.away_score) if (self.home_score is not None and self.away_score is not None) else None,  # Frontend expects 'score_diff'
            'sport': self.sport,
            'parlay_sport': self.parlay_sport,
            'bet_type': self.bet_type,
            'stat': self.stat_type,  # Frontend expects 'stat'
            'stat_type': self.stat_type,
            'bet_line_type': self.bet_line_type,
            'over_under': self.bet_line_type,  # Frontend expects 'over_under'
            'stat_add': self.bet_line_type,  # Frontend expects 'stat_add'
            'target': float(self.target_value) if self.target_value else None,  # Frontend expects 'target'
            'target_value': float(self.target_value) if self.target_value else None,
            'current': float(self.achieved_value) if self.achieved_value else None,  # Frontend expects 'current'
            'achieved_value': float(self.achieved_value) if self.achieved_value else None,
            'player_season_avg': float(self.player_season_avg) if self.player_season_avg else None,
            'player_last_5_avg': float(self.player_last_5_avg) if self.player_last_5_avg else None,
            'vs_opponent_avg': float(self.vs_opponent_avg) if self.vs_opponent_avg else None,
            'target_vs_season': float(self.target_vs_season) if self.target_vs_season else None,
            'original_leg_odds': self.original_leg_odds,
            'boosted_leg_odds': self.boosted_leg_odds,
            'final_leg_odds': self.final_leg_odds,
            'status': self.status,
            'is_hit': self.is_hit,
            'void_reason': self.void_reason,
            'current_quarter': self.current_quarter,
            'time_remaining': self.time_remaining,
            'home_score': self.home_score,
            'away_score': self.away_score,
            'is_home_game': self.is_home_game,
            'weather_conditions': self.weather_conditions,
            'injury_during_game': self.injury_during_game,
            'dnp_reason': self.dnp_reason,
            'leg_order': self.leg_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
