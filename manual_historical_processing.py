#!/usr/bin/env python3
"""
Manual trigger for historical bet processing
Run this on Render to manually execute the historical processing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from automation.historical_bet_processing import process_historical_bets_api

def manual_historical_processing():
    """Manually trigger historical bet processing"""
    with app.app_context():
        print("Starting manual historical bet processing...")
        try:
            process_historical_bets_api()
            print("Manual historical bet processing completed successfully")
        except Exception as e:
            print(f"Error during manual historical bet processing: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    manual_historical_processing()