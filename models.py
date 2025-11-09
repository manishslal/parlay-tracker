# models.py - Database models for multi-user parlay tracker
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import bcrypt
import json

db = SQLAlchemy()

# Association table for many-to-many relationship between users and bets
bet_users = db.Table('bet_users',
    db.Column('bet_id', db.Integer, db.ForeignKey('bets.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('is_primary_bettor', db.Boolean, default=False),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

class User(UserMixin, db.Model):
    """User model for authentication and bet ownership"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(80), nullable=True)  # Display name for UI
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Old one-to-many relationship (kept for backward compatibility during migration)
    bets = db.relationship('Bet', backref='owner', lazy='dynamic', foreign_keys='Bet.user_id')
    
    # New many-to-many relationship for shared bets
    shared_bets = db.relationship('Bet', secondary=bet_users, backref='users', lazy='dynamic')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def get_all_bets(self):
        """Get all bets visible to this user (owned + shared)"""
        from sqlalchemy import or_
        return Bet.query.join(bet_users, bet_users.c.bet_id == Bet.id).filter(
            bet_users.c.user_id == self.id
        )
    
    def get_primary_bets(self):
        """Get bets where this user is the primary bettor"""
        return Bet.query.join(bet_users, bet_users.c.bet_id == Bet.id).filter(
            bet_users.c.user_id == self.id,
            bet_users.c.is_primary_bettor == True
        )
    
    def to_dict(self):
        """Convert user to dictionary (excluding sensitive data)"""
        return {
            'id': self.id,
            'username': self.username,
            'display_name': self.display_name or self.username,  # Fallback to username if no display_name
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }
    
    def __repr__(self):
        return f'<User {self.username}>'


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


class BetLeg(db.Model):
    """BetLeg model for individual parlay legs"""
    __tablename__ = 'bet_legs'
    
    id = db.Column(db.Integer, primary_key=True)
    bet_id = db.Column(db.Integer, db.ForeignKey('bets.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'))
    
    # Player/Team Info
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
    is_home_game = db.Column(db.Boolean)
    
    # Bet Details
    bet_type = db.Column(db.String(50), nullable=False)
    bet_line_type = db.Column(db.String(20))  # 'over', 'under', etc.
    target_value = db.Column(db.Numeric(10, 2), nullable=False)
    achieved_value = db.Column(db.Numeric(10, 2))
    stat_type = db.Column(db.String(20))
    
    # Player Stats
    player_season_avg = db.Column(db.Numeric(10, 2))
    player_last_5_avg = db.Column(db.Numeric(10, 2))
    vs_opponent_avg = db.Column(db.Numeric(10, 2))
    target_vs_season = db.Column(db.Numeric(10, 2))
    
    # Odds
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
    
    # Additional Game Info
    weather_conditions = db.Column(db.String(100))
    injury_during_game = db.Column(db.Boolean)
    dnp_reason = db.Column(db.String(100))
    
    # Metadata
    leg_order = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<BetLeg {self.player_name} - {self.bet_type}>'


class Bet(db.Model):
    """Bet model for storing parlay data"""
    __tablename__ = 'bets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Bet identification (nullable because some old bets don't have IDs)
    bet_id = db.Column(db.String(100), nullable=True, index=True)
    
    # Bet type and site
    bet_type = db.Column(db.String(50), nullable=True)  # 'parlay', 'SGP', etc.
    betting_site = db.Column(db.String(50), nullable=True)
    
    # Bet status
    status = db.Column(db.String(20), default='pending')  # 'pending', 'won', 'lost', 'live'
    
    # Bet state flags
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # 1=active/live, 0=completed/historical
    is_archived = db.Column(db.Boolean, default=False, nullable=False)  # 1=archived, 0=not archived
    api_fetched = db.Column(db.String(3), default='No', nullable=False)  # 'Yes' if ESPN data fetched, 'No' otherwise
    
    # Bet data stored as JSON
    bet_data = db.Column(db.Text, nullable=False)  # Full bet JSON
    
    # New structured data columns (from migration)
    wager = db.Column(db.Numeric(10, 2))
    final_odds = db.Column(db.Integer)
    potential_winnings = db.Column(db.Numeric(10, 2))
    actual_winnings = db.Column(db.Numeric(10, 2))
    total_legs = db.Column(db.Integer, default=0)
    legs_won = db.Column(db.Integer, default=0)
    legs_lost = db.Column(db.Integer, default=0)
    legs_pending = db.Column(db.Integer, default=0)
    legs_live = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    bet_date = db.Column(db.String(20))  # Date from original bet (e.g., "2024-10-27")
    
    # Relationships
    bet_legs_rel = db.relationship('BetLeg', backref='bet', lazy='dynamic', cascade='all, delete-orphan')
    
    # Indexes for common queries
    __table_args__ = (
        db.Index('idx_user_status', 'user_id', 'status'),
        db.Index('idx_user_date', 'user_id', 'bet_date'),
    )
    
    def set_bet_data(self, bet_dict, preserve_status=False):
        """Store bet data as JSON string
        
        Args:
            bet_dict: Dictionary containing bet data
            preserve_status: If True, don't recalculate status from legs (useful during migration)
        """
        self.bet_data = json.dumps(bet_dict)
        
        # Extract commonly queried fields
        self.bet_id = bet_dict.get('bet_id', '')
        self.bet_type = bet_dict.get('type', 'parlay')
        self.betting_site = bet_dict.get('betting_site', 'Unknown')
        self.bet_date = bet_dict.get('bet_date', '')
        
        # Only recalculate status if not preserving existing status
        if not preserve_status:
            # Determine status from legs if present
            legs = bet_dict.get('legs', [])
            if legs:
                if all(leg.get('status') == 'won' for leg in legs):
                    self.status = 'won'
                elif any(leg.get('status') == 'lost' for leg in legs):
                    self.status = 'lost'
                elif any(leg.get('status') == 'live' for leg in legs):
                    self.status = 'live'
                else:
                    self.status = 'pending'
    
    def get_bet_data(self):
        """Parse and return bet data as dictionary"""
        return json.loads(self.bet_data)
    
    def add_user(self, user, is_primary=False):
        """Add a user to this bet with specified role"""
        # Check if user already has access
        existing = db.session.execute(
            bet_users.select().where(
                db.and_(
                    bet_users.c.bet_id == self.id,
                    bet_users.c.user_id == user.id
                )
            )
        ).fetchone()
        
        if not existing:
            stmt = bet_users.insert().values(
                bet_id=self.id,
                user_id=user.id,
                is_primary_bettor=is_primary
            )
            db.session.execute(stmt)
            db.session.commit()
            return True
        return False
    
    def remove_user(self, user):
        """Remove a user's access to this bet"""
        stmt = bet_users.delete().where(
            db.and_(
                bet_users.c.bet_id == self.id,
                bet_users.c.user_id == user.id
            )
        )
        db.session.execute(stmt)
        db.session.commit()
    
    def get_primary_bettor(self):
        """Get the username of the primary bettor"""
        result = db.session.execute(
            db.select(User.username).join(
                bet_users, bet_users.c.user_id == User.id
            ).where(
                bet_users.c.bet_id == self.id,
                bet_users.c.is_primary_bettor == True
            )
        ).fetchone()
        
        return result[0] if result else None
    
    def to_dict(self):
        """Convert bet to dictionary for API responses"""
        bet_dict = self.get_bet_data()
        bet_dict['db_id'] = self.id
        bet_dict['user_id'] = self.user_id
        bet_dict['bettor'] = self.get_primary_bettor()  # Add primary bettor name
        bet_dict['created_at'] = self.created_at.isoformat()
        bet_dict['updated_at'] = self.updated_at.isoformat()
        return bet_dict
    
    def to_dict_structured(self):
        """Convert bet to dictionary using structured database tables
        
        This method queries bet_legs and players tables instead of using the JSON blob.
        Includes jersey numbers and all relational data.
        """
        # Get bet-level data from columns
        bet_dict = {
            'db_id': self.id,
            'user_id': self.user_id,
            'bettor': self.get_primary_bettor(),
            'bet_id': self.bet_id or '',
            'betting_site': self.betting_site or 'Unknown',
            'status': self.status,
            'bet_date': self.bet_date or '',
            'created_at': self.created_at.isoformat() if self.created_at else '',
            'updated_at': self.updated_at.isoformat() if self.updated_at else '',
        }
        
        # Add financial data
        bet_dict['wager'] = float(self.wager) if self.wager else 0
        bet_dict['odds'] = self.final_odds or 0
        bet_dict['returns'] = float(self.potential_winnings) if self.potential_winnings else 0
        
        # Construct bet name from type and leg count
        if self.bet_type == 'SGP':
            bet_dict['name'] = f"{self.total_legs} Leg SGP"
        elif self.bet_type == 'Parlay':
            bet_dict['name'] = f"{self.total_legs} Pick Parlay"
        else:
            bet_dict['name'] = self.bet_type or 'Parlay'
        
        bet_dict['type'] = self.bet_type or 'Parlay'
        
        # Query bet legs with player data
        legs_query = db.session.query(BetLeg, Player).outerjoin(
            Player, BetLeg.player_id == Player.id
        ).filter(
            BetLeg.bet_id == self.id
        ).order_by(BetLeg.leg_order).all()
        
        legs = []
        for bet_leg, player in legs_query:
            # Get player team - use team_abbreviation from player table if available, otherwise player_team
            player_team = ''
            if player and player.team_abbreviation:
                player_team = player.team_abbreviation
            elif player and player.current_team:
                player_team = player.current_team
            elif bet_leg.player_team:
                player_team = bet_leg.player_team
            
            # Determine opponent (@ for away, no @ for home)
            opponent = ''
            if bet_leg.home_team and bet_leg.away_team:
                # Check if player's team matches away team (then opponent is @ home_team)
                if player_team and bet_leg.away_team and player_team.upper() in bet_leg.away_team.upper():
                    opponent = f"@ {bet_leg.home_team}"
                elif player_team and bet_leg.home_team and player_team.upper() in bet_leg.home_team.upper():
                    opponent = bet_leg.away_team
                else:
                    # Default: show away team as opponent
                    opponent = bet_leg.away_team
            
            leg_dict = {
                'player': bet_leg.player_name,
                'team': player_team,
                'position': bet_leg.player_position or (player.position if player else ''),
                'opponent': opponent,
                'stat': bet_leg.bet_type,
                'target': float(bet_leg.target_value) if bet_leg.target_value else 0,
                'current': float(bet_leg.achieved_value) if bet_leg.achieved_value else None,
                'status': bet_leg.status or 'pending',
                'gameId': bet_leg.game_id or '',
                'homeTeam': bet_leg.home_team,
                'awayTeam': bet_leg.away_team,
                # Add fields needed by process_parlay_data
                'home': bet_leg.home_team,  # process_parlay_data uses 'home'
                'away': bet_leg.away_team,  # process_parlay_data uses 'away'
                'game_date': bet_leg.game_date.strftime('%Y-%m-%d') if bet_leg.game_date else '',  # CRITICAL: process_parlay_data needs this
            }
            
            # Add jersey number if available from player table
            if player and player.jersey_number:
                leg_dict['jersey_number'] = player.jersey_number
                leg_dict['team_abbr'] = player.team_abbreviation or bet_leg.player_team
            
            # Add stat_add (over/under) if available
            if bet_leg.bet_line_type:
                leg_dict['stat_add'] = bet_leg.bet_line_type
            
            # Add live game data if available
            if bet_leg.home_score is not None:
                leg_dict['homeScore'] = bet_leg.home_score
            if bet_leg.away_score is not None:
                leg_dict['awayScore'] = bet_leg.away_score
            
            # Add game status (scheduled, in_progress, completed, final)
            if bet_leg.game_status:
                leg_dict['gameStatus'] = bet_leg.game_status
            
            # Add quarter/period info if available
            if bet_leg.current_quarter:
                leg_dict['currentPeriod'] = bet_leg.current_quarter
            
            # Calculate score_diff for spread/moneyline bets
            # score_diff = (bet team's score) - (opponent's score)
            if bet_leg.home_score is not None and bet_leg.away_score is not None:
                # Determine which team the bet is on
                if bet_leg.bet_type in ['spread', 'moneyline']:
                    # For team bets, player_name contains the team name
                    # Check if the bet team matches home or away
                    bet_team_name = bet_leg.player_name or player_team or ''
                    is_home_bet = False
                    
                    if bet_leg.home_team and bet_team_name:
                        # Check if bet team is home team
                        is_home_bet = (bet_team_name in bet_leg.home_team) or (bet_leg.home_team in bet_team_name)
                    
                    if is_home_bet:
                        leg_dict['score_diff'] = bet_leg.home_score - bet_leg.away_score
                    else:
                        leg_dict['score_diff'] = bet_leg.away_score - bet_leg.home_score
                elif player_team and bet_leg.home_team:
                    # For player props, check if player's team is home or away
                    is_home = player_team in bet_leg.home_team or bet_leg.home_team in player_team
                    score_diff = bet_leg.home_score - bet_leg.away_score if is_home else bet_leg.away_score - bet_leg.home_score
                    leg_dict['score_diff'] = score_diff
            
            legs.append(leg_dict)
        
        bet_dict['legs'] = legs
        
        # Fallback: Merge with JSON data to fill in missing fields
        try:
            json_data = self.get_bet_data()
            json_legs = json_data.get('legs', [])
            
            # Enrich each leg with JSON data if available
            for i, leg_dict in enumerate(legs):
                if i < len(json_legs):
                    json_leg = json_legs[i]
                    # Add missing fields from JSON
                    if not leg_dict.get('opponent') and json_leg.get('opponent'):
                        leg_dict['opponent'] = json_leg['opponent']
                    
                    # Always override with JSON data if available (structured DB may be incomplete)
                    if json_leg.get('home'):
                        leg_dict['homeTeam'] = json_leg['home']
                        leg_dict['home'] = json_leg['home']
                    if json_leg.get('away'):
                        leg_dict['awayTeam'] = json_leg['away']
                        leg_dict['away'] = json_leg['away']
                    if json_leg.get('game_date'):
                        leg_dict['game_date'] = json_leg['game_date']
                    
                    # Add scores from JSON if not in database
                    if not leg_dict.get('homeScore') and json_leg.get('homeScore') is not None:
                        leg_dict['homeScore'] = json_leg['homeScore']
                    if not leg_dict.get('awayScore') and json_leg.get('awayScore') is not None:
                        leg_dict['awayScore'] = json_leg['awayScore']
                    
                    # Calculate score_diff from JSON scores if needed for spread/moneyline
                    if not leg_dict.get('score_diff') and leg_dict.get('homeScore') is not None and leg_dict.get('awayScore') is not None:
                        if leg_dict.get('stat') in ['spread', 'moneyline']:
                            bet_team_name = leg_dict.get('player') or leg_dict.get('team') or ''
                            home_team = leg_dict.get('home', '')
                            is_home_bet = bet_team_name and home_team and (bet_team_name in home_team or home_team in bet_team_name)
                            
                            if is_home_bet:
                                leg_dict['score_diff'] = leg_dict['homeScore'] - leg_dict['awayScore']
                            else:
                                leg_dict['score_diff'] = leg_dict['awayScore'] - leg_dict['homeScore']
                    
                    # Also merge other potentially missing fields
                    if json_leg.get('stat_add'):
                        leg_dict['stat_add'] = json_leg['stat_add']
            
            # Preserve boost, sport, and other metadata
            if 'boost' in json_data:
                bet_dict['boost'] = json_data['boost']
            if 'sport' in json_data:
                bet_dict['sport'] = json_data['sport']
        except Exception as e:
            # Log but don't fail if JSON fallback has issues
            import logging
            logging.warning(f"JSON fallback failed: {e}")
        
        return bet_dict
    
    def __repr__(self):
        return f'<Bet {self.bet_id} - User {self.user_id}>'
