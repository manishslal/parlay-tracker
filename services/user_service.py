# Business logic for users

from models import Bet, db
from sqlalchemy import or_, text, and_

def get_user_bets_query(user, is_active=None, is_archived=None, status=None):
    """
    Get bets for a user, including both primary bets (user_id=user.id)
    and secondary bets (user.id in secondary_bettors array).
    """
    if not user or not hasattr(user, 'id'):
        return Bet.query.filter(db.text('0=1'))  # Always empty query
    
    # Build base query for primary bettor (user_id = user.id)
    primary_filter = Bet.user_id == user.id
    
    # Build filter for secondary bettors (user.id in secondary_bettors array)
    # PostgreSQL ARRAY @> operator checks if array contains element
    secondary_filter = db.text(f"secondary_bettors @> ARRAY[{user.id}]")
    
    # Combine both filters (OR - user is either primary or secondary)
    base_query = Bet.query.filter(or_(primary_filter, secondary_filter))
    
    # Apply additional filters
    if is_active is not None:
        base_query = base_query.filter_by(is_active=is_active)
    if is_archived is not None:
        base_query = base_query.filter_by(is_archived=is_archived)
    if status is not None:
        base_query = base_query.filter_by(status=status)
    
    return base_query

# Add more user-related service functions here
