from . import db
from datetime import datetime


class Team(db.Model):
    """Team model for storing NFL and NBA team information"""
    __tablename__ = 'teams'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic Team Info
    team_name = db.Column(db.String(100), nullable=False)
    team_name_short = db.Column(db.String(50))
    team_abbr = db.Column(db.String(10), nullable=False)
    espn_team_id = db.Column(db.String(50), unique=True)
    
    # Sport & League Info
    sport = db.Column(db.String(50), nullable=False)
    league = db.Column(db.String(50))
    conference = db.Column(db.String(50))
    division = db.Column(db.String(50))
    
    # Current Season Record
    games_played = db.Column(db.Integer, default=0)
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    ties = db.Column(db.Integer, default=0)
    win_percentage = db.Column(db.Numeric(5, 3))
    
    # Standings Info
    division_rank = db.Column(db.Integer)
    conference_rank = db.Column(db.Integer)
    league_rank = db.Column(db.Integer)
    playoff_seed = db.Column(db.Integer)
    games_behind = db.Column(db.Numeric(4, 1))
    streak = db.Column(db.String(20))
    
    # Team Details
    location = db.Column(db.String(100))
    nickname = db.Column(db.String(50))
    logo_url = db.Column(db.Text)
    color = db.Column(db.String(20))
    alternate_color = db.Column(db.String(20))
    
    # Status & Metadata
    is_active = db.Column(db.Boolean, default=True)
    season_year = db.Column(db.String(10))
    last_game_date = db.Column(db.Date)
    next_game_date = db.Column(db.Date)
    
    # API References
    api_data_url = db.Column(db.Text)
    last_stats_update = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert team to dictionary"""
        return {
            'id': self.id,
            'team_name': self.team_name,
            'team_name_short': self.team_name_short,
            'team_abbr': self.team_abbr,
            'espn_team_id': self.espn_team_id,
            'sport': self.sport,
            'conference': self.conference,
            'division': self.division,
            'wins': self.wins,
            'losses': self.losses,
            'ties': self.ties,
            'win_percentage': float(self.win_percentage) if self.win_percentage else None,
            'logo_url': self.logo_url,
            'color': self.color
        }
    
    def __repr__(self):
        return f'<Team {self.team_name} ({self.sport})>'