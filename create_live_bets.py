from app import app, db
from models import User, Bet, BetLeg
from datetime import datetime, date

def create_live_bets():
    print("Setting up diverse live test bets for today (2025-11-24)...")
    
    with app.app_context():
        # 1. Get test user
        user = User.query.filter_by(username='testuser').first()
        if not user:
            print("Error: 'testuser' not found. Please run verify_connection.py first.")
            return

        # 2. Clear existing bets
        print(f"Clearing existing bets for user {user.username}...")
        # Delete legs first to avoid foreign key constraints (though cascade might handle it, explicit is safer)
        user_bets = Bet.query.filter_by(user_id=user.id).all()
        for bet in user_bets:
            BetLeg.query.filter_by(bet_id=bet.id).delete()
            db.session.delete(bet)
        db.session.commit()
        print("Existing bets cleared.")

        today = date(2025, 11, 24)
        
        # --- Bet 1: Likely WIN (Low Targets) ---
        # "Safe" parlay
        bet1_data = {
            "betting_site": "DraftKings",
            "wager": 100.0,
            "potential_winnings": 150.0,
            "final_odds": -200,
            "bet_date": today.isoformat(),
            "bet_type": "parlay",
            "legs": [
                {
                    "player_name": "Stephen Curry",
                    "team_name": "Golden State Warriors",
                    "home_team": "Golden State Warriors",
                    "away_team": "Utah Jazz",
                    "stat_type": "points",
                    "target_value": 10.5, # Very low for Curry
                    "bet_line_type": "over",
                    "sport": "NBA",
                    "game_date": today.isoformat()
                },
                {
                    "player_name": "Donovan Mitchell",
                    "team_name": "Cleveland Cavaliers",
                    "home_team": "Toronto Raptors",
                    "away_team": "Cleveland Cavaliers",
                    "stat_type": "points",
                    "target_value": 15.5, # Low for Mitchell
                    "bet_line_type": "over",
                    "sport": "NBA",
                    "game_date": today.isoformat()
                }
            ]
        }
        
        # --- Bet 2: Likely LOSS (High Targets) ---
        # "Lotto" parlay
        bet2_data = {
            "betting_site": "FanDuel",
            "wager": 10.0,
            "potential_winnings": 1000.0,
            "final_odds": 10000,
            "bet_date": today.isoformat(),
            "bet_type": "parlay",
            "legs": [
                {
                    "player_name": "Stephen Curry",
                    "team_name": "Golden State Warriors",
                    "home_team": "Golden State Warriors",
                    "away_team": "Utah Jazz",
                    "stat_type": "points",
                    "target_value": 50.5, # Very high
                    "bet_line_type": "over",
                    "sport": "NBA",
                    "game_date": today.isoformat()
                },
                {
                    "player_name": "Scottie Barnes",
                    "team_name": "Toronto Raptors",
                    "home_team": "Toronto Raptors",
                    "away_team": "Cleveland Cavaliers",
                    "stat_type": "rebounds",
                    "target_value": 15.5, # High
                    "bet_line_type": "over",
                    "sport": "NBA",
                    "game_date": today.isoformat()
                }
            ]
        }

        # --- Bet 3: Variety Stats (Threes, Blocks, Assists) ---
        bet3_data = {
            "betting_site": "MGM",
            "wager": 25.0,
            "potential_winnings": 125.0,
            "final_odds": 400,
            "bet_date": today.isoformat(),
            "bet_type": "SGP",
            "legs": [
                {
                    "player_name": "Stephen Curry",
                    "team_name": "Golden State Warriors",
                    "home_team": "Golden State Warriors",
                    "away_team": "Utah Jazz",
                    "stat_type": "three_pointers_made", # Correct internal name usually mapped
                    "target_value": 3.5,
                    "bet_line_type": "over",
                    "sport": "NBA",
                    "game_date": today.isoformat()
                },
                {
                    "player_name": "Evan Mobley",
                    "team_name": "Cleveland Cavaliers",
                    "home_team": "Toronto Raptors",
                    "away_team": "Cleveland Cavaliers",
                    "stat_type": "blocks",
                    "target_value": 1.5,
                    "bet_line_type": "over",
                    "sport": "NBA",
                    "game_date": today.isoformat()
                },
                {
                    "player_name": "Darius Garland",
                    "team_name": "Cleveland Cavaliers",
                    "home_team": "Toronto Raptors",
                    "away_team": "Cleveland Cavaliers",
                    "stat_type": "assists",
                    "target_value": 6.5,
                    "bet_line_type": "over",
                    "sport": "NBA",
                    "game_date": today.isoformat()
                }
            ]
        }

        # --- Bet 4: Team Props (Spread & Moneyline) ---
        bet4_data = {
            "betting_site": "Caesars",
            "wager": 50.0,
            "potential_winnings": 95.0,
            "final_odds": -110,
            "bet_date": today.isoformat(),
            "bet_type": "Straight",
            "legs": [
                {
                    "player_name": "Golden State Warriors", # Team name for team props
                    "team_name": "Golden State Warriors",
                    "home_team": "Golden State Warriors",
                    "away_team": "Utah Jazz",
                    "stat_type": "point_spread", # or 'spread'
                    "target_value": -5.5,
                    "bet_line_type": "spread", # Special handling might be needed
                    "sport": "NBA",
                    "game_date": today.isoformat()
                },
                 {
                    "player_name": "Cleveland Cavaliers",
                    "team_name": "Cleveland Cavaliers",
                    "home_team": "Toronto Raptors",
                    "away_team": "Cleveland Cavaliers",
                    "stat_type": "moneyline",
                    "target_value": 0,
                    "bet_line_type": "moneyline",
                    "sport": "NBA",
                    "game_date": today.isoformat()
                }
            ]
        }
        
        from app import save_bet_to_db
        
        save_bet_to_db(user.id, bet1_data, skip_duplicate_check=True)
        print("Created Bet 1: Likely Win (Low Targets)")
        
        save_bet_to_db(user.id, bet2_data, skip_duplicate_check=True)
        print("Created Bet 2: Likely Loss (High Targets)")
        
        save_bet_to_db(user.id, bet3_data, skip_duplicate_check=True)
        print("Created Bet 3: Variety Stats")
        
        save_bet_to_db(user.id, bet4_data, skip_duplicate_check=True)
        print("Created Bet 4: Team Props")
        
        print("Done! 4 new bets created.")

if __name__ == "__main__":
    create_live_bets()
