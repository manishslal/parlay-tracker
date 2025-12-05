
from app import app, db
from routes.bets import transform_extracted_bet_data
import json

def reproduce_atd_target():
    with app.app_context():
        print("Testing ATD target value parsing...")
        
        # Simulate data from frontend/OCR
        mock_data = {
            'bet_id': 'TEST_ATD_001',
            'bet_site': 'DraftKings',
            'bet_type': 'parlay',
            'wager_amount': 10.0,
            'legs': [
                {
                    'player': 'Derrick Henry',
                    'team': 'Baltimore Ravens',
                    'stat': 'Anytime Touchdown Scorer',
                    'line': 0, # Simulating what the frontend might send if no line is found
                    'odds': -150
                },
                {
                    'player': 'Lamar Jackson',
                    'team': 'Baltimore Ravens',
                    'stat': 'Anytime Touchdown',
                    'line': None, # Simulating missing line
                    'odds': +120
                }
            ]
        }
        
        print(f"Input Data: {json.dumps(mock_data, indent=2)}")
        
        # Run transformation
        transformed = transform_extracted_bet_data(mock_data)
        
        print("\nTransformed Data:")
        for leg in transformed['legs']:
            print(f"  Stat: {leg['stat_type']}")
            print(f"  Bet Type: {leg['bet_type']}")
            print(f"  Target Value: {leg['target_value']}")
            
            if leg['stat_type'] == 'anytime_touchdown' and leg['target_value'] != 1.0:
                 print("  ❌ FAILURE: Target value should be 1.0 for ATD")
            elif leg['stat_type'] == 'anytime_touchdown' and leg['target_value'] == 1.0:
                 print("  ✅ SUCCESS: Target value is 1.0")
            else:
                 print(f"  ℹ️ Note: Stat type is {leg['stat_type']}")

if __name__ == "__main__":
    reproduce_atd_target()
