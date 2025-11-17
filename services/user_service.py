# Business logic for users

from models import Bet, db

def get_user_bets_query(user, is_active=None, is_archived=None, status=None):
    if not user or not hasattr(user, 'id'):
        return Bet.query.filter(db.text('0=1'))  # Always empty query
    query = Bet.query.filter_by(user_id=user.id)
    if is_active is not None:
        query = query.filter_by(is_active=is_active)
    if is_archived is not None:
        query = query.filter_by(is_archived=is_archived)
    if status is not None:
        query = query.filter_by(status=status)
    return query

# Add more user-related service functions here
