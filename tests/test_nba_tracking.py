import unittest
from services.bet_service import calculate_bet_value

class TestNBATracking(unittest.TestCase):
    def setUp(self):
        # Mock NBA Game Data with Boxscore
        self.mock_game_data = {
            "score": {"home": 110, "away": 105},
            "teams": {"home": "Lakers", "away": "Warriors"},
            "boxscore": [
                {
                    "team": {"displayName": "Lakers"},
                    "statistics": [
                        {
                            "name": "offensive",  # ESPN sometimes uses 'offensive' or just implied general stats
                            "labels": ["MIN", "PTS", "REB", "AST", "STL", "BLK", "TO", "3PT"],
                            "athletes": [
                                {
                                    "athlete": {"displayName": "LeBron James"},
                                    "stats": ["35", "28", "10", "8", "2", "1", "3", "2-5"]
                                }
                            ]
                        }
                    ]
                }
            ],
            "scoring_plays": []
        }
        
        # Helper to inject 'general' category if needed by _get_player_stat_from_boxscore
        # The actual function iterates through all categories, so we just need to match the structure
        # In our implementation we used "general" as category name for NBA stats in stat_map
        # But _get_player_stat_from_boxscore checks cat.get("name").lower() == category_name.lower()
        # So we need to make sure our mock data has the right category name or we adjust the test
        
        # Let's adjust the mock to match what _get_player_stat_from_boxscore expects
        # In utils.py, _get_player_stat_from_boxscore iterates through team_box["statistics"]
        # We mapped "points" to ("general", "PTS")
        # So we need a statistic group named "general"
        
        self.mock_game_data["boxscore"][0]["statistics"][0]["name"] = "general"

    def test_points(self):
        bet = {"player": "LeBron James", "stat": "points"}
        val = calculate_bet_value(bet, self.mock_game_data)
        self.assertEqual(val, 28)

    def test_rebounds(self):
        bet = {"player": "LeBron James", "stat": "rebounds"}
        val = calculate_bet_value(bet, self.mock_game_data)
        self.assertEqual(val, 10)

    def test_assists(self):
        bet = {"player": "LeBron James", "stat": "assists"}
        val = calculate_bet_value(bet, self.mock_game_data)
        self.assertEqual(val, 8)
        
    def test_threes(self):
        bet = {"player": "LeBron James", "stat": "three_pointers_made"}
        val = calculate_bet_value(bet, self.mock_game_data)
        self.assertEqual(val, 2)  # Should parse "2-5" as 2

    def test_pra(self):
        bet = {"player": "LeBron James", "stat": "points_rebounds_assists"}
        val = calculate_bet_value(bet, self.mock_game_data)
        self.assertEqual(val, 28 + 10 + 8)

    def test_double_double(self):
        bet = {"player": "LeBron James", "stat": "double_double"}
        val = calculate_bet_value(bet, self.mock_game_data)
        self.assertEqual(val, 1) # 28 PTS, 10 REB

    def test_triple_double(self):
        bet = {"player": "LeBron James", "stat": "triple_double"}
        val = calculate_bet_value(bet, self.mock_game_data)
        self.assertEqual(val, 0) # Only 8 AST

if __name__ == '__main__':
    unittest.main()
