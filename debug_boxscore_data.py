from app import app
from services.bet_service import fetch_game_details_from_espn
import json

def debug_boxscore():
    print("=== Checking Boxscore in Game Data ===\n")
    with app.app_context():
        game_data = fetch_game_details_from_espn(
            game_date='2024-11-24',
            away_team='Cleveland Cavaliers',
            home_team='Toronto Raptors',
            sport='NBA'
        )
        
        if not game_data:
            print("❌ No game data")
            return
        
        print("Keys in game_data:", list(game_data.keys()))
        
        boxscore = game_data.get('boxscore', [])
        print(f"\nBoxscore type: {type(boxscore)}")
        print(f"Boxscore length: {len(boxscore)}")
        
        if boxscore:
            print(f"\nFirst team keys: {list(boxscore[0].keys())}")
            stats = boxscore[0].get('statistics', [])
            print(f"Stats categories: {len(stats)}")
            if stats:
                print(f"First cat name: '{stats[0].get('name')}'")
                athletes = stats[0].get('athletes', [])
                print(f"Athletes: {len(athletes)}")
                if athletes:
                    for ath in athletes[:3]:
                        print(f"  - {ath.get('athlete', {}).get('displayName')}")

if __name__ == "__main__":
    debug_boxscore()
