# Centralized SQLAlchemy db instance
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

from .user import User
from .bet import Bet
from .bet_leg import BetLeg
from .player import Player
from .team import Team