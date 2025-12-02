from helpers.utils import _get_touchdowns

# Mock Data
player_name = "Patrick Mahomes"

# Mock Boxscore (No rushing/receiving TDs)
boxscore = [
    {
        "statistics": [
            {
                "name": "passing",
                "labels": ["TD"],
                "athletes": [
                    {
                        "athlete": {"displayName": "Patrick Mahomes"},
                        "stats": ["3"]  # 3 Passing TDs
                    }
                ]
            },
            {
                "name": "rushing",
                "labels": ["TD"],
                "athletes": [
                    {
                        "athlete": {"displayName": "Patrick Mahomes"},
                        "stats": ["0"]  # 0 Rushing TDs
                    }
                ]
            }
        ]
    }
]

# Mock Scoring Plays (Passing TD where Mahomes is a participant)
scoring_plays = [
    {
        "type": {"text": "Passing Touchdown"},
        "text": "Patrick Mahomes 5 Yd Pass to Travis Kelce",
        "participants": [
            {"displayName": "Patrick Mahomes"}, # Passer
            {"displayName": "Travis Kelce"}     # Receiver
        ]
    }
]

# Test
td_count = _get_touchdowns(player_name, boxscore, scoring_plays)
print(f"Player: {player_name}")
print(f"Calculated TDs: {td_count}")
print(f"Expected TDs: 0 (Passing TDs should not count for ATD)")

if td_count > 0:
    print("FAIL: Passing TD counted as Anytime TD")
else:
    print("PASS: Passing TD correctly ignored")
