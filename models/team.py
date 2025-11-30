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

    @staticmethod
    def get_team_by_name_cached(team_name):
        """Get team by name or abbreviation using a cache to avoid DB hits."""
        if not team_name:
            return None
            
        # Initialize cache if needed
        if not hasattr(Team, '_team_cache'):
            Team._team_cache = {}
            Team._team_cache_time = 0
            
        import time
        current_time = time.time()
        
        # Refresh cache every hour
        if current_time - getattr(Team, '_team_cache_time', 0) > 3600:
            all_teams = Team.query.all()
            Team._team_cache = {t.team_name.lower(): t for t in all_teams}
            # Also index by abbreviation and short name
            for t in all_teams:
                if t.team_abbr:
                    Team._team_cache[t.team_abbr.lower()] = t
                if t.team_name_short:
                    Team._team_cache[t.team_name_short.lower()] = t
            Team._team_cache_time = current_time
            
        team_name_lower = team_name.lower()
        
        # Try exact match from cache
        if team_name_lower in Team._team_cache:
            return Team._team_cache[team_name_lower]
        
        # Try partial match if not found
        for key, t in Team._team_cache.items():
            if team_name_lower in key or key in team_name_lower:
                return t
        
        # Fallback for specific known issues
        if team_name_lower.startswith('los angeles'):
            # Try to disambiguate based on sport if possible, but here we only have name
            # If it's just "Los Angeles", we can't do much.
            # But if it's "Los Angeles Lakers" and it didn't match above, something is wrong with the cache keys.
            # Let's try matching against specific known LA teams
            la_teams = ['lakers', 'clippers', 'rams', 'chargers', 'dodgers', 'angels', 'kings', 'galaxy', 'la fc']
            for suffix in la_teams:
                if suffix in team_name_lower:
                    # Try to find the team with this suffix in cache
                    for key, t in Team._team_cache.items():
                        if suffix in key:
                            return t
                            
        return None