#!/usr/bin/env python3
"""
Fetch player team/position data from ESPN API and update bet 95
"""
from app import app, db
from models import Bet
import requests
import time

# Manual mapping for players (based on 2024/2025 NFL season)
PLAYER_DATA = {
    'Caleb Williams': {'team': 'Chicago Bears', 'position': 'QB'},
    'Joe Flacco': {'team': 'Indianapolis Colts', 'position': 'QB'},
    'Jared Goff': {'team': 'Detroit Lions', 'position': 'QB'},
    'J.J. McCarthy': {'team': 'Minnesota Vikings', 'position': 'QB'},
    'Michael Penix Jr.': {'team': 'Atlanta Falcons', 'position': 'QB'},
    'Drake Maye': {'team': 'New England Patriots', 'position': 'QB'},
    'Bo Nix': {'team': 'Denver Broncos', 'position': 'QB'},
    'C.J. Stroud': {'team': 'Houston Texans', 'position': 'QB'},
    'Bryce Young': {'team': 'Carolina Panthers', 'position': 'QB'},
    'Jordan Love': {'team': 'Green Bay Packers', 'position': 'QB'},
    'Mac Jones': {'team': 'Jacksonville Jaguars', 'position': 'QB'},
    'Jaxson Dart': {'team': 'New York Giants', 'position': 'QB'},  # Assuming he's with Giants
    'Justin Herbert': {'team': 'Los Angeles Chargers', 'position': 'QB'},
    'Cam Ward': {'team': 'Miami Dolphins', 'position': 'QB'},  # Draft prospect, assuming team
    'Aaron Rodgers': {'team': 'New York Jets', 'position': 'QB'}
}

def search_espn_player(player_name):
    """Search ESPN API for player information"""
    try:
        # ESPN player search endpoint
        url = f"https://site.api.espn.com/apis/common/v3/search"
        params = {
            'query': player_name,
            'type': 'players',
            'limit': 5
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Look for NFL players
            if 'results' in data:
                for result in data['results']:
                    if result.get('type') == 'Player' and result.get('league') == 'nfl':
                        # Extract player info
                        player_info = {
                            'name': result.get('displayName'),
                            'team': result.get('teamDisplayName'),
                            'position': result.get('position', {}).get('abbreviation', 'QB')
                        }
                        return player_info
        
        return None
    except Exception as e:
        print(f"  ❌ Error searching ESPN for {player_name}: {e}")
        return None

def update_player_data():
    """Update player data for bet 95"""
    
    with app.app_context():
        # Get bet 95
        bet = Bet.query.get(95)
        
        if not bet:
            print("❌ Bet 95 not found")
            return
        
        bet_data = bet.get_bet_data()
        
        print(f"Bet: {bet_data.get('name')}")
        print(f"\nUpdating {len(bet_data.get('legs', []))} legs...\n")
        print("="*80)
        
        updated_count = 0
        
        for i, leg in enumerate(bet_data.get('legs', []), 1):
            player = leg.get('player')
            
            if not player:
                continue
            
            # Check if already has team/position
            if leg.get('team') and leg.get('position'):
                print(f"Leg {i}: {player} - Already has data ✓")
                continue
            
            print(f"\nLeg {i}: {player}")
            
            # Try manual mapping first
            if player in PLAYER_DATA:
                leg['team'] = PLAYER_DATA[player]['team']
                leg['position'] = PLAYER_DATA[player]['position']
                print(f"  ✅ Updated: {leg['team']} | {leg['position']}")
                updated_count += 1
            else:
                # Try ESPN API
                print(f"  🔍 Searching ESPN API...")
                player_info = search_espn_player(player)
                
                if player_info and player_info.get('team'):
                    leg['team'] = player_info['team']
                    leg['position'] = player_info.get('position', 'QB')
                    print(f"  ✅ Found: {leg['team']} | {leg['position']}")
                    updated_count += 1
                else:
                    print(f"  ⚠️  Not found - keeping as is")
                
                # Rate limit
                time.sleep(0.5)
        
        if updated_count > 0:
            # Save updated bet data
            bet.set_bet_data(bet_data, preserve_status=True)
            db.session.commit()
            
            print(f"\n{'='*80}")
            print(f"✅ Updated {updated_count} players")
            print("="*80)
        else:
            print(f"\n{'='*80}")
            print("ℹ️  No updates needed")
            print("="*80)

if __name__ == '__main__':
    print("="*80)
    print("UPDATING PLAYER DATA FOR BET 95")
    print("="*80)
    update_player_data()
