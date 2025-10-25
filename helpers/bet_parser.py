"""
Bet data parsing and formatting helpers
"""

from datetime import datetime
from typing import Dict, List

def parse_bet_date(date_str: str) -> datetime:
    """Parse date string in format M/D/YY to datetime"""
    # Since all bets are from 2025
    month, day, year = date_str.split('/')
    return datetime(2025, int(month), int(day))

def parse_betting_site(bet_id: str) -> str:
    """Determine betting site from bet ID"""
    if bet_id.startswith("O/"):
        return "FanDuel"
    elif bet_id.startswith("DK"):
        return "DraftKings"
    else:
        return "Unknown"

def bet_exists(bet_id: str, existing_bets: List[Dict]) -> bool:
    """
    Check if a bet with the given bet_id already exists in the bet list
    Returns True if bet exists, False otherwise
    """
    for bet in existing_bets:
        if bet.get("bet_id") == bet_id:
            return True
    return False

def get_parlay_date_keys(bet: Dict) -> tuple:
    """
    Get sorting keys for a parlay based on leg dates.
    Returns: (earliest_date, latest_date) for sorting
    
    Sort order:
    - Primary: earliest_date (ascending) - shows newer parlays first
    - Secondary: latest_date (descending) - breaks ties by latest leg
    """
    legs = bet.get("legs", [])
    if not legs:
        # If no legs, use a default far-past date
        return ("1900-01-01", "1900-01-01")
    
    dates = []
    for leg in legs:
        game_date = leg.get("game_date")
        if game_date:
            dates.append(game_date)
    
    if not dates:
        return ("1900-01-01", "1900-01-01")
    
    earliest_date = min(dates)  # Earliest leg date (date option 2)
    latest_date = max(dates)    # Latest leg date (date option 1)
    
    return (earliest_date, latest_date)

def sort_historical_bets(bets: List[Dict]) -> List[Dict]:
    """
    Sort historical bets by game dates.
    Primary sort: earliest leg date (descending - newer first)
    Secondary sort: latest leg date (descending - newer first)
    """
    return sorted(bets, key=lambda bet: get_parlay_date_keys(bet), reverse=True)

def calculate_bet_status(bet: Dict) -> str:
    """
    Calculate bet status based on leg outcomes.
    Returns: "Won" if all legs hit, "Loss" if any leg missed
    """
    legs = bet.get('legs', [])
    if not legs:
        return "Loss"
    
    # Check if all legs have their targets met
    all_hit = True
    for leg in legs:
        stat = leg.get('stat', '')
        current = leg.get('current', 0)
        target = leg.get('target', 0)
        
        # For anytime_touchdown, first_touchdown, moneyline: binary (1 = hit, 0 = miss)
        if stat in ['anytime_touchdown', 'first_touchdown', 'moneyline']:
            if current == 0:
                all_hit = False
                break
        # For passing_yards_under: current should be under target
        elif 'under' in stat:
            if current >= target:
                all_hit = False
                break
        # For all other stats: current should meet or exceed target
        else:
            if current < target:
                all_hit = False
                break
    
    return "Won" if all_hit else "Loss"

def extract_bet_date(bet: Dict) -> str:
    """
    Extract bet date from bet object.
    Priority: 
    1. Direct bet_date field (when bet was placed)
    2. Earliest game_date from legs (fallback)
    3. Parse from bet name (fallback)
    """
    # First priority: use the explicit bet_date field if it exists
    if 'bet_date' in bet and bet['bet_date']:
        return bet['bet_date']
    
    # Fallback 1: Try to get earliest game_date from legs
    legs = bet.get('legs', [])
    dates = []
    for leg in legs:
        game_date = leg.get('game_date')
        if game_date and game_date != 'N/A':
            dates.append(game_date)
    
    if dates:
        # Return earliest date
        return min(dates)
    
    # Fallback 2: try to parse from name (e.g., "10/12 Parlay" -> "2025-10-12")
    name = bet.get('name', '')
    if '/' in name:
        try:
            date_part = name.split()[0]  # "10/12"
            month, day = date_part.split('/')
            # Assume 2025 for all bets
            return f"2025-{int(month):02d}-{int(day):02d}"
        except:
            pass
    
    # Default fallback
    return "2025-01-01"
