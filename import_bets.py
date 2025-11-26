import json
import os
from datetime import datetime
from app import app
from models import db, Bet, BetLeg, User

def import_bets():
    file_path = 'data/user_1_manishslal_bets.json'
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, 'r') as f:
        bets_data = json.load(f)

    print(f"Found {len(bets_data)} bets to import.")

    with app.app_context():
        # Ensure user exists
        user = User.query.get(1)
        if not user:
            print("Creating default user (ID 1)...")
            user = User(id=1, username="manishslal", email="manishslal@example.com") # Dummy email
            db.session.add(user)
            db.session.commit()

        count = 0
        for bet_dict in bets_data:
            # Create Bet object
            bet = Bet()
            bet.user_id = 1
            
            # Use the model's helper to populate fields
            bet.set_bet_data(bet_dict)
            
            # Ensure status is set (default to pending if not in dict)
            if not bet.status:
                bet.status = 'pending'
            
            # Add to session to get an ID (needed for legs)
            db.session.add(bet)
            db.session.flush() # Get ID

            # Process Legs
            legs_data = bet_dict.get('legs', [])
            for i, leg_data in enumerate(legs_data):
                leg = BetLeg()
                leg.bet_id = bet.id
                leg.leg_order = i
                
                # Map fields
                leg.player_name = leg_data.get('player_name') or leg_data.get('team_name') or "Unknown"
                leg.player_team = leg_data.get('player_team') or leg_data.get('team_name')
                leg.stat_type = leg_data.get('stat_type')
                leg.bet_type = leg_data.get('bet_type')
                leg.target_value = leg_data.get('target_value') if leg_data.get('target_value') is not None else 0
                leg.bet_line_type = leg_data.get('bet_line_type')
                leg.sport = leg_data.get('sport')
                leg.game_date = leg_data.get('game_date')
                leg.status = leg_data.get('status', 'pending')
                leg.home_team = leg_data.get('home_team')
                leg.away_team = leg_data.get('away_team')
                
                # Handle odds (might be null)
                odds_val = leg_data.get('odds')
                if odds_val:
                    try:
                        leg.odds = int(str(odds_val).replace('+', ''))
                    except:
                        pass

                db.session.add(leg)
            
            count += 1
            if count % 100 == 0:
                print(f"Processed {count} bets...")
        
        try:
            db.session.commit()
            print(f"Successfully imported {count} bets.")
        except Exception as e:
            db.session.rollback()
            print(f"Error importing bets: {e}")

if __name__ == "__main__":
    import_bets()
