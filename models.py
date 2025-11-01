# models.py - Database models for multi-user parlay tracker
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import bcrypt
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication and bet ownership"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship to bets
    bets = db.relationship('Bet', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def to_dict(self):
        """Convert user to dictionary (excluding sensitive data)"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }
    
    def __repr__(self):
        return f'<User {self.username}>'


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
    
    # Bet data stored as JSON
    bet_data = db.Column(db.Text, nullable=False)  # Full bet JSON
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    bet_date = db.Column(db.String(20))  # Date from original bet (e.g., "2024-10-27")
    
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
    
    def to_dict(self):
        """Convert bet to dictionary for API responses"""
        bet_dict = self.get_bet_data()
        bet_dict['db_id'] = self.id
        bet_dict['user_id'] = self.user_id
        bet_dict['created_at'] = self.created_at.isoformat()
        bet_dict['updated_at'] = self.updated_at.isoformat()
        return bet_dict
    
    def __repr__(self):
        return f'<Bet {self.bet_id} - User {self.user_id}>'
