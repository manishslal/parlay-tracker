"""
Check if total_points legs have away/home team data
"""
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Bet

with app.app_context():
    # Get the live bets (status pending or live)
    live_bets = Bet.query.filter(Bet.status.in_(['pending', 'live'])).all()
    
    print(f"\n{'='*80}")
    print(f"Found {len(live_bets)} live bets")
    print(f"{'='*80}\n")
    
    for bet in live_bets:
        bet_data = bet.get_bet_data()
        print(f"Bet ID: {bet.id}")
        print(f"Name: {bet_data.get('name', 'N/A')}")
        print(f"Status: {bet.status}")
        print(f"\nLegs:")
        
        for i, leg in enumerate(bet_data.get('legs', []), 1):
            stat = leg.get('stat', 'N/A')
            print(f"\n  Leg {i}:")
            print(f"    Stat: {stat}")
            print(f"    Player: {leg.get('player', 'N/A')}")
            print(f"    Team: {leg.get('team', 'N/A')}")
            print(f"    Away: {leg.get('away', 'N/A')}")
            print(f"    Home: {leg.get('home', 'N/A')}")
            print(f"    Target: {leg.get('target', 'N/A')}")
            
            # Check if this is a total_points leg
            if 'total_points' in stat.lower():
                print(f"    ⚠️  TOTAL POINTS LEG")
                if not leg.get('away') or not leg.get('home'):
                    print(f"    ❌ Missing away/home data!")
        
        print(f"\n{'-'*80}\n")
