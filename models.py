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
    api_fetched = db.Column(db.String(3), default='No', nullable=False)  # 'Yes' if ESPN data fetched, 'No' otherwise
    
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
    
    def __repr__(self):
        return f'<Bet {self.bet_id} - User {self.user_id}>'
