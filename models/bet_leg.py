
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

    def _get_current_value(self):
        """
        Get the current value for this bet leg.
        For moneyline/spread bets, use score_diff.
        For other bets, use achieved_value.
        """
        # For moneyline and spread bets, use score_diff (current game difference)
        if self.bet_type in ['moneyline', 'spread']:
            if self.home_score is not None and self.away_score is not None:
                # Calculate which team the bet is on
                bet_team_name = self.player_name or self.player_team or ''
                is_home_bet = False
                
                if self.home_team and bet_team_name:
                    is_home_bet = (bet_team_name in self.home_team) or (self.home_team in bet_team_name)
                
                score_diff = self.home_score - self.away_score if is_home_bet else self.away_score - self.home_score
                return float(score_diff)
        
        # For all other bets, use achieved_value
        if self.achieved_value is not None:
            return float(self.achieved_value)
        
        return None

    def to_dict(self):
        base_dict = {
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
            'target': float(self.target_value) if self.target_value is not None else None,  # Frontend expects 'target'
            'target_value': float(self.target_value) if self.target_value is not None else None,
            # For moneyline/spread bets, use score_diff; for others, use achieved_value
            'current': self._get_current_value(),  # Frontend expects 'current'
            'achieved_value': float(self.achieved_value) if self.achieved_value is not None else None,
            'player_season_avg': float(self.player_season_avg) if self.player_season_avg is not None else None,
            'player_last_5_avg': float(self.player_last_5_avg) if self.player_last_5_avg is not None else None,
            'vs_opponent_avg': float(self.vs_opponent_avg) if self.vs_opponent_avg is not None else None,
            'target_vs_season': float(self.target_vs_season) if self.target_vs_season is not None else None,
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
            'homeScore': self.home_score,  # Frontend expects camelCase
            'awayScore': self.away_score,  # Frontend expects camelCase
            'is_home_game': self.is_home_game,
            'weather_conditions': self.weather_conditions,
            'injury_during_game': self.injury_during_game,
            'dnp_reason': self.dnp_reason,
            'leg_order': self.leg_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # Add jersey and team branding info
        self._add_branding_info(base_dict)
        
        # Add display values for moneyline and spread bets
        display_values = self.get_display_values()
        base_dict.update(display_values)
        
        return base_dict

    def _add_branding_info(self, data):
        """Add jersey number, team colors, and logo to the dictionary."""
        from models.player import Player
        from models.team import Team
        
        # Default values
        data['player_jersey_number'] = None
        data['team_color'] = '#000000' # Default black
        data['team_alternate_color'] = '#ffffff' # Default white
        data['team_logo'] = '/media/unknown-logo.svg'
        
        # 1. Fetch Player Jersey Number
        if self.player_id:
            player = Player.query.get(self.player_id)
            if player and player.jersey_number:
                data['player_jersey_number'] = player.jersey_number
        
        # If not found by ID (e.g. new player), try matching by name and sport
        if data['player_jersey_number'] is None and self.player_name and self.sport:
            player = Player.query.filter_by(player_name=self.player_name, sport=self.sport).first()
            if player and player.jersey_number:
                data['player_jersey_number'] = player.jersey_number

        # 2. Fetch Team Colors and Logo
        # Try to match team by name OR abbreviation
        team_name = self.player_team or self.home_team or self.away_team
        if team_name:
            # Try exact match first
            team = Team.query.filter(Team.team_name.ilike(team_name)).first()
            
            # If no exact match, try abbreviation
            if not team:
                team = Team.query.filter(Team.team_abbr.ilike(team_name)).first()
            
            # If still no match, try partial match (e.g. "Lakers" in "Los Angeles Lakers")
            if not team:
                team = Team.query.filter(Team.team_name.ilike(f'%{team_name}%')).first()
            
            # If still no match, try checking if the first word is an abbreviation (e.g. "ATL Falcons" -> "ATL")
            if not team:
                first_word = team_name.split(' ')[0]
                if len(first_word) <= 3: # Abbreviations are usually short
                    team = Team.query.filter(Team.team_abbr.ilike(first_word)).first()
                
            if team:
                if team.color:
                    # Ensure hex prefix
                    color = team.color.strip()
                    if not color.startswith('#'):
                        color = f"#{color}"
                    data['team_color'] = color
                
                if team.alternate_color:
                    # Ensure hex prefix
                    alt_color = team.alternate_color.strip()
                    if not alt_color.startswith('#'):
                        alt_color = f"#{alt_color}"
                    data['team_alternate_color'] = alt_color

                if team.logo_url:
                    data['team_logo'] = team.logo_url
        
        # Logic to determine WHICH color to use for the jersey (Home vs Away)
        # If player's team is the home team, use primary color. Else use alternate/white.
        is_home = False
        if self.player_team and self.home_team:
            if self.player_team.lower() in self.home_team.lower() or self.home_team.lower() in self.player_team.lower():
                is_home = True
        
        data['jersey_primary_color'] = data['team_color'] if is_home else (data['team_alternate_color'] or '#ffffff')
        data['jersey_secondary_color'] = '#ffffff' if is_home else data['team_color']

    def get_display_values(self):
        """Calculate display values for Current and Progress fields for moneyline and spread bets."""
        current_display = None
        progress_display = None
        progress_color = None
        
        # Skip display value generation for moneyline, anytime_touchdown, spread, and total_points bets
        # These are better handled by the frontend's specialized display logic
        if self.stat_type and self.stat_type.lower() in ['moneyline', 'anytime_touchdown', 'anytime_td', 'spread', 'total_points']:
            return {
                'current_display': current_display,
                'progress_display': progress_display,
                'progress_color': progress_color
            }
        
        # For other bet types, calculate display values
        # (This section is for future use with other bet types that need backend display values)
        
        return {
            'current_display': current_display,
            'progress_display': progress_display,
            'progress_color': progress_color
        }
