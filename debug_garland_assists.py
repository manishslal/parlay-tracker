from app import app
from services.bet_service import fetch_game_details_from_espn
from helpers.utils import _get_player_stat_from_boxscore
import json

def debug_garland():
    print("Debugging Garland assists...")
    with app.app_context():
        # Fetch the Cavs vs Raptors game
        game_data = fetch_game_details_from_espn(
            game_date='2024-11-24',
            away_team='Cleveland Cavaliers',
            home_team='Toronto Raptors',
            sport='NBA'
        )
        
        if not game_data:
            print("❌ No game data found")
            return
        
        print(f"✅ Game found: {game_data.get('teams', {}).get('away')} @ {game_data.get('teams', {}).get('home')}")
        print(f"Score: {game_data.get('score', {})}")
        print(f"Status: {game_data.get('statusTypeName')}")
        
        # Try to get Garland's assists
        boxscore = game_data.get('boxscore', [])
        print(f"\nBoxscore teams: {len(boxscore)}")
        
        # Try different variations
        variations = [
            ('Darius Garland', '', 'AST'),
            ('D. Garland', '', 'AST'),
            ('Garland', '', 'AST'),
        ]
        
        for player_name, category, stat_label in variations:
            assists = _get_player_stat_from_boxscore(player_name, category, stat_label, boxscore)
            print(f"\n'{player_name}' ({category}, {stat_label}): {assists}")
        
        # Print boxscore structure for debugging
        print("\n=== Boxscore Structure ===")
        for i, team_box in enumerate(boxscore):
            print(f"\nTeam {i}:")
            stats = team_box.get('statistics', [])
            print(f"  Stats categories: {len(stats)}")
            for cat in stats:
                cat_name = cat.get('name', 'NO_NAME')
                print(f"    - Category: '{cat_name}'")
                athletes = cat.get('athletes', [])
                print(f"      Athletes: {len(athletes)}")
                if athletes:
                    # Show first few athletes
                    for athlete in athletes[:3]:
                        name = athlete.get('athlete', {}).get('displayName', 'Unknown')
                        stats_data = athlete.get('stats', [])
                        print(f"        {name}: {stats_data}")

if __name__ == "__main__":
    debug_garland()
