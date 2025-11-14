#!/usr/bin/env python3
"""
Debug ESPN game fetching for live bets
"""
from app import app, fetch_game_details_from_espn
from models import Bet
from datetime import datetime

def debug_live_games():
    """Check what's happening with live game fetching"""
    
    with app.app_context():
        # Get live bets
        live_bets = Bet.query.filter_by(status='live', is_active=True).all()
        
        print(f"📊 Found {len(live_bets)} live bets\n")
        
        for bet in live_bets:
            bet_data = bet.get_bet_data()
            print(f"\n{'='*70}")
            print(f"Bet: {bet_data.get('name')}")
            print('='*70)
            
            # Check first leg
            if bet_data.get('legs'):
                leg = bet_data['legs'][0]
                game_date = leg.get('game_date')
                away = leg.get('away')
                home = leg.get('home')
                
                print(f"\nFirst leg details:")
                print(f"  Game Date: {game_date}")
                print(f"  Away: {away}")
                print(f"  Home: {home}")
                
                # Try fetching
                print(f"\n🌐 Fetching from ESPN...")
                game_data = fetch_game_details_from_espn(game_date, away, home)
                
                if game_data:
                    print(f"  ✅ Game found!")
                    print(f"  Status: {game_data.get('statusTypeName')}")
                    print(f"  Score: {game_data.get('score')}")
                    print(f"  Period: {game_data.get('period')}")
                    print(f"  Clock: {game_data.get('clock')}")
                else:
                    print(f"  ❌ Game not found")
                    
                    # Try with today's date
                    today = datetime.now().strftime('%Y-%m-%d')
                    print(f"\n  🔄 Trying with today's date: {today}")
                    game_data = fetch_game_details_from_espn(today, away, home)
                    
                    if game_data:
                        print(f"  ✅ Game found with today's date!")
                        print(f"  Status: {game_data.get('statusTypeName')}")
                        print(f"  Score: {game_data.get('score')}")
                    else:
                        print(f"  ❌ Still not found")

if __name__ == '__main__':
    debug_live_games()
