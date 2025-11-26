import unittest
from services.bet_service import calculate_bet_value

class TestNFLTracking(unittest.TestCase):
    def setUp(self):
        # Mock NFL Game Data with Boxscore
        self.mock_game_data = {
            "score": {"home": 24, "away": 17},
            "teams": {"home": "Steelers", "away": "Ravens"},
            "boxscore": [
                {
                    "team": {"displayName": "Steelers"},
                    "statistics": [
                        {
                            "name": "kicking",
                            "labels": ["FG", "PCT", "LONG", "XP", "PTS"],
                            "athletes": [
                                {
                                    "athlete": {"displayName": "Chris Boswell"},
                                    "stats": ["4/4", "100.0", "50", "2/2", "14"]
                                }
                            ]
                        },
                        {
                            "name": "defensive",
                            "labels": ["TOT", "SOLO", "SACKS", "TFL", "PD", "QB HTS", "TD"],
                            "athletes": [
                                {
                                    "athlete": {"displayName": "T.J. Watt"},
                                    "stats": ["5", "4", "2.0", "2", "0", "3", "0"]
                                }
                            ]
                        },
                        {
                            "name": "interceptions",
                            "labels": ["INT", "YDS", "TD"],
                            "athletes": [
                                {
                                    "athlete": {"displayName": "Minkah Fitzpatrick"},
                                    "stats": ["1", "20", "0"]
                                }
                            ]
                        },
                        {
                            "name": "passing",
                            "labels": ["C/ATT", "YDS", "AVG", "TD", "INT", "SACKS", "QBR", "RTG"],
                            "athletes": [
                                {
                                    "athlete": {"displayName": "Patrick Mahomes II"},
                                    "stats": ["20/30", "250", "8.3", "2", "0", "1", "85.0", "110.0"]
                                }
                            ]
                        }
                    ]
                }
            ],
            "scoring_plays": []
        }

    def test_field_goals(self):
        bet = {"player": "Chris Boswell", "stat": "field_goals_made"}
        val = calculate_bet_value(bet, self.mock_game_data)
        self.assertEqual(val, 4) # Should parse "4/4" as 4

    def test_extra_points(self):
        bet = {"player": "Chris Boswell", "stat": "extra_points_made"}
        val = calculate_bet_value(bet, self.mock_game_data)
        self.assertEqual(val, 2) # Should parse "2/2" as 2

    def test_sacks(self):
        bet = {"player": "T.J. Watt", "stat": "sacks"}
        val = calculate_bet_value(bet, self.mock_game_data)
        self.assertEqual(val, 2)

    def test_solo_tackles(self):
        bet = {"player": "T.J. Watt", "stat": "solo_tackles"}
        val = calculate_bet_value(bet, self.mock_game_data)
        self.assertEqual(val, 4)

    def test_interceptions(self):
        bet = {"player": "Minkah Fitzpatrick", "stat": "defensive_interceptions"}
        val = calculate_bet_value(bet, self.mock_game_data)
        self.assertEqual(val, 1)

    def test_name_matching(self):
        # Search for "Patrick Mahomes" but data has "Patrick Mahomes II"
        bet = {"player": "Patrick Mahomes", "stat": "passing_yards"}
        val = calculate_bet_value(bet, self.mock_game_data)
        self.assertEqual(val, 250)

if __name__ == '__main__':
    unittest.main()
