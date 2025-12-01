import json
from app import app, db
from models import User, Bet
from flask_login import login_user

def verify_functionality():
    print("Starting functionality verification...")
    
    with app.test_client() as client:
        with app.app_context():
            # 1. Setup Test User
            print("\n1. Setting up test user...")
            user = User.query.filter_by(username='testuser').first()
            if not user:
                user = User(username='testuser', email='test@example.com')
                user.set_password('password')
                db.session.add(user)
                db.session.commit()
                print("Created 'testuser'.")
            else:
                print("User 'testuser' already exists.")
            
            # Simulate Login
            with client.session_transaction() as sess:
                sess['_user_id'] = str(user.id)
                sess['_fresh'] = True
            
            # 2. Test Bet Creation (via save_extracted_bet endpoint)
            print("\n2. Testing Bet Creation...")
            bet_payload = {
                "betting_site": "DraftKings",
                "wager": 10.0,
                "potential_winnings": 20.0,
                "final_odds": 100,
                "bet_date": "2024-10-27",
                "legs": [
                    {
                        "player_name": "Test Player",
                        "team_name": "Test Team",
                        "stat_type": "points",
                        "target_value": 15.5,
                        "bet_line_type": "over",
                        "sport": "NBA"
                    }
                ]
            }
            
            # Note: The route URL depends on the blueprint prefix. 
            # app.py registers bets_bp without prefix, so it should be at root or /api/bets depending on the blueprint definition.
            # Let's assume /api/bets/save_extracted based on common patterns, but I'll check the blueprint definition if this fails.
            # Looking at routes/bets.py, it likely defines routes like @bets_bp.route('/save_extracted', methods=['POST'])
            # And app.py registers it with no url_prefix? No, app.py says: app.register_blueprint(bets_bp) # No url_prefix
            
            # Correct URL found in routes/bets.py: /api/save-extracted-bet
            response = client.post('/api/save-extracted-bet', 
                                 data=json.dumps(bet_payload),
                                 content_type='application/json')
            
            if response.status_code == 200:
                print("Bet creation successful!")
                data = json.loads(response.data)
                bet_id = data.get('bet', {}).get('id') # Response structure is {'bet': {'id': ...}}
                print(f"Created Bet ID: {bet_id}")
            else:
                print(f"Bet creation failed: {response.status_code} - {response.data}")

            # 3. Verify Database State
            print("\n3. Verifying Database State...")
            if 'bet_id' in locals():
                bet = Bet.query.get(bet_id)
                if bet:
                    print(f"Bet found in DB: {bet}")
                    print(f"Secondary Bettors (JSON): {bet.secondary_bettors} (Type: {type(bet.secondary_bettors)})")
                    print(f"Watchers (JSON): {bet.watchers} (Type: {type(bet.watchers)})")
                    
                    # Verify JSON type is working (should be list, not string if SQLAlchemy handles it, 
                    # but SQLite might return list if using proper JSON type, or we might need to cast)
                    if isinstance(bet.secondary_bettors, list):
                         print("Column type check passed: secondary_bettors is a list.")
                    else:
                         print(f"Column type warning: secondary_bettors is {type(bet.secondary_bettors)}")

                else:
                    print("Bet not found in DB!")
            
            # 4. Test Bet Retrieval (Historical)
            print("\n4. Testing Bet Retrieval (Historical)...")
            response = client.get('/historical')
            if response.status_code == 200:
                print("Historical bets retrieval successful!")
                # print(response.data[:200]) # Print first 200 chars
            else:
                print(f"Historical retrieval failed: {response.status_code}")

if __name__ == "__main__":
    verify_functionality()
