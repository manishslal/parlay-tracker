from app import app
from helpers.utils import _get_player_stat_from_boxscore
from services.bet_service import fetch_game_details_from_espn

def test_direct_extraction():
    print("=== Testing Direct _get_player_stat_from_boxscore ===\n")
    with app.app_context():
        # Fetch game data
        game_data = fetch_game_details_from_espn(
            game_date='2024-11-24',
            away_team='Cleveland Cavaliers',
            home_team='Toronto Raptors',
            sport='NBA'
        )
        
        if not game_data:
            print("❌ No game data")
            return
        
        boxscore = game_data.get('boxscore', [])
        print(f"Boxscore teams: {len(boxscore)}")
        
        # Print category details
        print("\nCategory details:")
        for i, team_box in enumerate(boxscore):
            print(f"Team {i}:")
            for cat in team_box.get('statistics', []):
                cat_name = cat.get('name')
                print(f"  Name: {repr(cat_name)} (type: {type(cat_name)})")
        
        # Test extraction
        print("\n=== Extraction Tests ===")
        tests = [
            ('Darius Garland', '', 'AST'),
            ('Darius Garland', 'None', 'AST'),
            ('Darius Garland', None, 'AST'),
        ]
        
        for player, cat, label in tests:
            val = _get_player_stat_from_boxscore(player, cat, label, boxscore)
            print(f"Player='{player}', Cat={repr(cat)}, Label='{label}': Val={val}")

if __name__ == "__main__":
    test_direct_extraction()
