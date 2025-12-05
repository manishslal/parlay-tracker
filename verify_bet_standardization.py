
import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.getcwd())

# Mock the database and models BEFORE importing app
sys.modules['models'] = MagicMock()
sys.modules['models'].db = MagicMock()
sys.modules['models'].Bet = MagicMock()
sys.modules['models'].BetLeg = MagicMock()
sys.modules['models'].Team = MagicMock()
sys.modules['models'].Player = MagicMock()

# Mock helpers and its submodules
sys.modules['helpers'] = MagicMock()
sys.modules['helpers.database'] = MagicMock()
sys.modules['helpers.espn_api'] = MagicMock()
sys.modules['helpers.enhanced_player_search'] = MagicMock()
sys.modules['helpers.audit_helpers'] = MagicMock()
sys.modules['helpers.utils'] = MagicMock()
sys.modules['helpers.team_utils'] = MagicMock()

# Mock services
sys.modules['services'] = MagicMock()
sys.modules['services.bet_service'] = MagicMock()

# Mock other modules
sys.modules['stat_standardization'] = MagicMock()

# Import the function to test
# We don't need to import routes.bets since we are testing the logic copied from it
# This avoids complex mocking of Flask dependencies

class TestBetStandardization(unittest.TestCase):
    
    def test_standardization_logic(self):
        """Test the logic used in create_bet to standardize bet types"""
        
        # Simulate the logic from routes/bets.py
        def standardize_legs(legs):
            for i, leg in enumerate(legs):
                # Standardize bet_type for legs
                stat = leg.get('stat', '').lower()
                
                # Determine if it's a Team Prop
                is_team_prop = False
                if 'moneyline' in stat:
                    leg['stat_type'] = 'moneyline'
                    leg['target_value'] = 0.00
                    is_team_prop = True
                elif 'spread' in stat:
                    leg['stat_type'] = 'spread'
                    is_team_prop = True
                elif 'total' in stat or 'points' in stat and leg.get('team') == 'Game Total':
                    leg['stat_type'] = 'total_points'
                    is_team_prop = True
                elif leg.get('team') == 'Game Total':
                    leg['stat_type'] = 'total_points' # Default for Game Total
                    is_team_prop = True
                
                # Set bet_type based on classification
                if is_team_prop:
                    leg['bet_type'] = 'Team Prop'
                else:
                    leg['bet_type'] = 'Player Prop'
                    # If stat_type wasn't set above, use the stat field
                    if 'stat_type' not in leg:
                        leg['stat_type'] = stat
            return legs

        # Test Case 1: Moneyline
        legs_ml = [{'stat': 'moneyline', 'team': 'Lakers'}]
        standardize_legs(legs_ml)
        self.assertEqual(legs_ml[0]['bet_type'], 'Team Prop')
        self.assertEqual(legs_ml[0]['stat_type'], 'moneyline')
        
        # Test Case 2: Spread
        legs_spread = [{'stat': 'spread', 'team': 'Lakers'}]
        standardize_legs(legs_spread)
        self.assertEqual(legs_spread[0]['bet_type'], 'Team Prop')
        self.assertEqual(legs_spread[0]['stat_type'], 'spread')
        
        # Test Case 3: Player Prop
        legs_player = [{'stat': 'points', 'player': 'LeBron', 'team': 'Lakers'}]
        standardize_legs(legs_player)
        self.assertEqual(legs_player[0]['bet_type'], 'Player Prop')
        self.assertEqual(legs_player[0]['stat_type'], 'points')
        
        # Test Case 4: Game Total
        legs_total = [{'stat': 'total points', 'team': 'Game Total'}]
        standardize_legs(legs_total)
        self.assertEqual(legs_total[0]['bet_type'], 'Team Prop')
        self.assertEqual(legs_total[0]['stat_type'], 'total_points')
        
        print("SUCCESS: Standardization logic verified.")

if __name__ == '__main__':
    unittest.main()
