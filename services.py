"""
services.py - Business logic and ESPN API integration for Parlay Tracker
"""
from helpers.utils import (
    get_events,
    calculate_bet_value,
    process_parlay_data,
    sort_parlays_by_date,
    compute_parlay_returns_from_odds
)
from models import Bet, BetLeg, User

# Example: Move ESPN API and bet processing logic here
# ...move service functions from app.py here as you modularize...
