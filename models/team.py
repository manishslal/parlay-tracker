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
        from sqlalchemy.exc import PendingRollbackError, OperationalError
        
        for attempt in range(2):
            try:
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
                t = None
                if team_name_lower in Team._team_cache:
                    t = Team._team_cache[team_name_lower]
                
                # Try partial match if not found
                if not t:
                    for key, team in Team._team_cache.items():
                        if team_name_lower in key or key in team_name_lower:
                            t = team
                            break
                
                # Fallback for specific known issues
                if not t and team_name_lower.startswith('los angeles'):
                    la_teams = ['lakers', 'clippers', 'rams', 'chargers', 'dodgers', 'angels', 'kings', 'galaxy', 'la fc']
                    for suffix in la_teams:
                        if suffix in team_name_lower:
                            for key, team in Team._team_cache.items():
                                if suffix in key:
                                    t = team
                                    break
                            if t: break

                if t:
                    return db.session.merge(t)
                return None

            except (PendingRollbackError, OperationalError) as e:
                if "rollback" in str(e).lower() or isinstance(e, PendingRollbackError):
                    if attempt == 0:
                        db.session.rollback()
                        continue
                # If it's not a rollback error or we already retried, log and return None
                print(f"Error in get_team_by_name_cached: {e}")
                return None
            except Exception as e:
                print(f"Unexpected error in get_team_by_name_cached: {e}")
                return None
        return None

    @staticmethod
    def get_team_abbr_by_name_cached(team_name):
        """Get just the team abbreviation string from cache.
        This avoids db.session.merge() which is expensive and causes transaction issues.
        """
        # Reuse the logic from get_team_by_name_cached but return string only
        # We can call the main method to ensure cache is populated/refreshed
        # But we need to be careful not to trigger the merge if we can avoid it.
        
        if not team_name:
            return ""
            
        # Ensure cache is initialized
        if not hasattr(Team, '_team_cache'):
            # Trigger cache load by calling the main method with a dummy or just copying the init logic
            # Let's copy the init logic to be safe and efficient
            Team.get_team_by_name_cached("ensure_cache_init")
            
        team_name_lower = team_name.lower()
        t = None
        
        # 1. Exact match
        if team_name_lower in Team._team_cache:
            t = Team._team_cache[team_name_lower]
            
        # 2. Partial match
        if not t:
            for key, team in Team._team_cache.items():
                if team_name_lower in key or key in team_name_lower:
                    t = team
                    break
                    
        # 3. Fallback (LA teams etc)
        if not t and team_name_lower.startswith('los angeles'):
            la_teams = ['lakers', 'clippers', 'rams', 'chargers', 'dodgers', 'angels', 'kings', 'galaxy', 'la fc']
            for suffix in la_teams:
                if suffix in team_name_lower:
                    for key, team in Team._team_cache.items():
                        if suffix in key:
                            t = team
                            break
                    if t: break
                    
        if t and t.team_abbr:
            return t.team_abbr
            
        return ""