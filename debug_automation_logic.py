import unittest
from unittest.mock import MagicMock
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

# Mock app and db before importing modules that use them
mock_app_module = MagicMock()
sys.modules['app'] = mock_app_module
mock_models_module = MagicMock()
sys.modules['models'] = mock_models_module
sys.modules['helpers.audit_helpers'] = MagicMock()

# Import the module under test
from automation.bet_status_management import auto_move_bets_no_live_legs

class TestBetStatusAutomation(unittest.TestCase):
    def setUp(self):
        # Reset mocks
        mock_app_module.reset_mock()
        mock_models_module.reset_mock()
        
    def test_auto_move_bets_no_live_legs_won(self):
        # Setup mock bet
        mock_bet_obj = MagicMock()
        mock_bet_obj.id = 1
        mock_bet_obj.status = 'live'
        
        # Configure Bet query
        mock_models_module.Bet.query.filter.return_value.all.return_value = [mock_bet_obj]
        
        # Setup mock legs (all won, all final)
        leg1 = MagicMock()
        leg1.status = 'won'
        leg1.game_status = 'STATUS_FINAL'
        leg1.achieved_value = 10
        
        leg2 = MagicMock()
        leg2.status = 'won'
        leg2.game_status = 'STATUS_FINAL'
        leg2.achieved_value = 20
        
        # Configure BetLeg query
        mock_models_module.BetLeg.query.filter.return_value.with_for_update.return_value.all.return_value = [leg1, leg2]
        
        # Run function
        auto_move_bets_no_live_legs()
        
        # Verify bet status updated to 'won'
        self.assertEqual(mock_bet_obj.status, 'won')
        self.assertFalse(mock_bet_obj.is_active)
        
    def test_auto_move_bets_no_live_legs_lost(self):
        # Setup mock bet
        mock_bet_obj = MagicMock()
        mock_bet_obj.id = 2
        mock_bet_obj.status = 'live'
        
        # Configure Bet query
        mock_models_module.Bet.query.filter.return_value.all.return_value = [mock_bet_obj]
        
        # Setup mock legs (one lost)
        leg1 = MagicMock()
        leg1.status = 'won'
        leg1.game_status = 'STATUS_FINAL'
        leg1.achieved_value = 10
        
        leg2 = MagicMock()
        leg2.status = 'lost'
        leg2.game_status = 'STATUS_FINAL'
        leg2.achieved_value = 5
        
        # Configure BetLeg query
        mock_models_module.BetLeg.query.filter.return_value.with_for_update.return_value.all.return_value = [leg1, leg2]
        
        # Run function
        auto_move_bets_no_live_legs()
        
        # Verify bet status updated to 'lost'
        self.assertEqual(mock_bet_obj.status, 'lost')
        self.assertFalse(mock_bet_obj.is_active)

if __name__ == '__main__':
    unittest.main()
