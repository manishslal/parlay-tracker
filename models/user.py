
from flask_login import UserMixin
from models import db
from datetime import datetime
import bcrypt

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(80), nullable=True)  # Display name for UI
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    user_role = db.Column(db.String(20), default='user', nullable=False)  # 'admin' or 'user'
    
    # Relationship to bets owned by this user
    bets = db.relationship('Bet', backref='owner', lazy='dynamic', foreign_keys='Bet.user_id')

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
        except ValueError:
            # Invalid hash format - this user needs password reset
            print(f"WARNING: User {self.username} has invalid password hash format")
            return False
    
    def is_admin(self):
        """Check if user has admin role"""
        return self.user_role == 'admin'
    
    def to_dict(self):
        """Convert user to dictionary (excluding sensitive data)"""
        return {
            'id': self.id,
            'username': self.username,
            'display_name': self.display_name or self.username,  # Fallback to username if no display_name
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'user_role': self.user_role or 'user'
        }
