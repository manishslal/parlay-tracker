"""
App configuration settings. Add environment-specific configs as needed.
"""
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///parlays.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 2592000
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_DURATION = 2592000

class DevConfig(Config):
    DEBUG = True

class ProdConfig(Config):
    DEBUG = False
