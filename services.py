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

def get_user_bets_query(user, is_active=None, is_archived=None, status=None):
    print(f"[DEBUG] get_user_bets_query called: user={getattr(user, 'id', None)}, is_active={is_active}, is_archived={is_archived}, status={status}")
    if not user or not hasattr(user, 'id'):
        print("[DEBUG] get_user_bets_query: user missing or invalid, returning empty query")
        return Bet.query.filter(db.text('0=1'))  # Always empty query
    query = Bet.query.filter_by(user_id=user.id)
    if is_active is not None:
        query = query.filter_by(is_active=is_active)
    if is_archived is not None:
        query = query.filter_by(is_archived=is_archived)
    if status is not None:
        query = query.filter_by(status=status)
    print(f"[DEBUG] get_user_bets_query: returning query {query}")
    return query

# Example: Move ESPN API and bet processing logic here
# ...move service functions from app.py here as you modularize...
