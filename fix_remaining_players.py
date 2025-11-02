#!/usr/bin/env python3
"""
Fix the 4 remaining players without team/position data
"""
from app import app, db
from models import Bet

# Correct data for the 4 players (based on user's info)
MISSING_PLAYERS = {
    'Bryce Young': {'team': 'Carolina Panthers', 'position': 'QB'},
    'Jaxson Dart': {'team': 'New York Giants', 'position': 'QB'},
    'Cam Ward': {'team': 'Tennessee Titans', 'position': 'QB'},
    'C.J. Stroud': {'team': 'Houston Texans', 'position': 'QB'}
}

def fix_remaining_players():
    """Update the 4 players that are still missing data"""
    
    with app.app_context():
        bet = Bet.query.get(95)
        
        if not bet:
            print("❌ Bet 95 not found")
            return
        
        bet_data = bet.get_bet_data()
        
        print(f"Bet: {bet_data.get('name')}\n")
        print("="*80)
        
        updated_count = 0
        
        for i, leg in enumerate(bet_data.get('legs', []), 1):
            player = leg.get('player')
            
            if not player or player not in MISSING_PLAYERS:
                continue
            
            # Check if missing data
            if not leg.get('team') or not leg.get('position'):
                print(f"Leg {i}: {player}")
                leg['team'] = MISSING_PLAYERS[player]['team']
                leg['position'] = MISSING_PLAYERS[player]['position']
                print(f"  ✅ Updated: {leg['team']} | {leg['position']}\n")
                updated_count += 1
        
        if updated_count > 0:
            bet.set_bet_data(bet_data, preserve_status=True)
            db.session.commit()
            
            print("="*80)
            print(f"✅ Updated {updated_count} players")
        else:
            print("="*80)
            print("ℹ️  All players already have data")
        
        print("="*80)

if __name__ == '__main__':
    print("="*80)
    print("FIXING 4 REMAINING PLAYERS")
    print("="*80 + "\n")
    fix_remaining_players()
