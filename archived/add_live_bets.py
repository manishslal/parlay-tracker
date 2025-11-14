#!/usr/bin/env python3
"""
Add two new live bets from screenshots
"""
from app import app, db
from models import Bet, User
from datetime import datetime

def add_live_bets():
    """Add the two bets from screenshots"""
    
    with app.app_context():
        # Get the user (assuming first user)
        user = User.query.first()
        if not user:
            print("❌ No user found")
            return
        
        print(f"Adding bets for user: {user.username}\n")
        
        # Bet 1: 7 leg parlay
        bet1 = {
            "bet_id": "O/0240915/0000064",
            "name": "7 leg parlay",
            "type": "parlay",
            "betting_site": "DraftKings",
            "bet_date": "2025-11-02",
            "wager": 10.00,
            "potential_payout": 215.83,
            "odds": "+2058",
            "legs": [
                {
                    "game_date": "2025-11-02",
                    "away": "Minnesota Vikings",
                    "home": "Detroit Lions",
                    "stat": "total_points",
                    "target": 47.5,
                    "over_under": "under"
                },
                {
                    "game_date": "2025-11-02",
                    "away": "San Francisco 49ers",
                    "home": "New York Giants",
                    "team": "San Francisco 49ers",
                    "stat": "spread",
                    "target": -2.5
                },
                {
                    "game_date": "2025-11-02",
                    "away": "Indianapolis Colts",
                    "home": "Pittsburgh Steelers",
                    "team": "Indianapolis Colts",
                    "stat": "moneyline",
                    "target": 1
                },
                {
                    "game_date": "2025-11-02",
                    "away": "Atlanta Falcons",
                    "home": "New England Patriots",
                    "team": "New England Patriots",
                    "stat": "moneyline",
                    "target": 1
                },
                {
                    "game_date": "2025-11-02",
                    "away": "Los Angeles Chargers",
                    "home": "Tennessee Titans",
                    "team": "Los Angeles Chargers",
                    "stat": "moneyline",
                    "target": 1
                },
                {
                    "game_date": "2025-11-02",
                    "away": "New Orleans Saints",
                    "home": "Los Angeles Rams",
                    "team": "Los Angeles Rams",
                    "stat": "moneyline",
                    "target": 1
                },
                {
                    "game_date": "2025-11-04",
                    "away": "Arizona Cardinals",
                    "home": "Dallas Cowboys",
                    "team": "Dallas Cowboys",
                    "stat": "moneyline",
                    "target": 1
                }
            ]
        }
        
        # Bet 2: 15 leg Same Game Parlay+
        bet2 = {
            "bet_id": "O/0240915/0000065",
            "name": "15 leg Same Game Parlay+",
            "type": "SGP+",
            "betting_site": "DraftKings",
            "bet_date": "2025-11-02",
            "wager": 5.00,
            "potential_payout": 57.69,
            "odds": "+1053",
            "legs": [
                # Chicago Bears @ Cincinnati Bengals
                {
                    "game_date": "2025-11-02",
                    "away": "Chicago Bears",
                    "home": "Cincinnati Bengals",
                    "player": "Caleb Williams",
                    "stat": "passing_yards",
                    "target": 175,
                    "over_under": "over"
                },
                {
                    "game_date": "2025-11-02",
                    "away": "Chicago Bears",
                    "home": "Cincinnati Bengals",
                    "player": "Joe Flacco",
                    "stat": "passing_yards",
                    "target": 175,
                    "over_under": "over"
                },
                # Minnesota Vikings @ Detroit Lions
                {
                    "game_date": "2025-11-02",
                    "away": "Minnesota Vikings",
                    "home": "Detroit Lions",
                    "player": "Jared Goff",
                    "stat": "passing_yards",
                    "target": 175,
                    "over_under": "over"
                },
                {
                    "game_date": "2025-11-02",
                    "away": "Minnesota Vikings",
                    "home": "Detroit Lions",
                    "player": "J.J. McCarthy",
                    "stat": "passing_yards",
                    "target": 150,
                    "over_under": "over"
                },
                # Atlanta Falcons @ New England Patriots
                {
                    "game_date": "2025-11-02",
                    "away": "Atlanta Falcons",
                    "home": "New England Patriots",
                    "player": "Michael Penix Jr.",
                    "stat": "passing_yards",
                    "target": 175,
                    "over_under": "over"
                },
                {
                    "game_date": "2025-11-02",
                    "away": "Atlanta Falcons",
                    "home": "New England Patriots",
                    "player": "Drake Maye",
                    "stat": "passing_yards",
                    "target": 175,
                    "over_under": "over"
                },
                # Denver Broncos @ Houston Texans
                {
                    "game_date": "2025-11-02",
                    "away": "Denver Broncos",
                    "home": "Houston Texans",
                    "player": "Bo Nix",
                    "stat": "passing_yards",
                    "target": 150,
                    "over_under": "over"
                },
                {
                    "game_date": "2025-11-02",
                    "away": "Denver Broncos",
                    "home": "Houston Texans",
                    "player": "C.J. Stroud",
                    "stat": "passing_yards",
                    "target": 150,
                    "over_under": "over"
                },
                # Carolina Panthers @ Green Bay Packers
                {
                    "game_date": "2025-11-02",
                    "away": "Carolina Panthers",
                    "home": "Green Bay Packers",
                    "player": "Bryce Young",
                    "stat": "passing_yards",
                    "target": 125,
                    "over_under": "over"
                },
                {
                    "game_date": "2025-11-02",
                    "away": "Carolina Panthers",
                    "home": "Green Bay Packers",
                    "player": "Jordan Love",
                    "stat": "passing_yards",
                    "target": 175,
                    "over_under": "over"
                },
                # San Francisco 49ers @ New York Giants
                {
                    "game_date": "2025-11-02",
                    "away": "San Francisco 49ers",
                    "home": "New York Giants",
                    "player": "Mac Jones",
                    "stat": "passing_yards",
                    "target": 175,
                    "over_under": "over"
                },
                {
                    "game_date": "2025-11-02",
                    "away": "San Francisco 49ers",
                    "home": "New York Giants",
                    "player": "Jaxson Dart",
                    "stat": "passing_yards",
                    "target": 150,
                    "over_under": "over"
                },
                # Los Angeles Chargers @ Tennessee Titans
                {
                    "game_date": "2025-11-02",
                    "away": "Los Angeles Chargers",
                    "home": "Tennessee Titans",
                    "player": "Justin Herbert",
                    "stat": "passing_yards",
                    "target": 175,
                    "over_under": "over"
                },
                {
                    "game_date": "2025-11-02",
                    "away": "Los Angeles Chargers",
                    "home": "Tennessee Titans",
                    "player": "Cam Ward",
                    "stat": "passing_yards",
                    "target": 150,
                    "over_under": "over"
                },
                # Indianapolis Colts @ Pittsburgh Steelers
                {
                    "game_date": "2025-11-02",
                    "away": "Indianapolis Colts",
                    "home": "Pittsburgh Steelers",
                    "player": "Aaron Rodgers",
                    "stat": "passing_yards",
                    "target": 175,
                    "over_under": "over"
                }
            ]
        }
        
        # Add bet 1
        db_bet1 = Bet(
            user_id=user.id,
            status='live',
            is_active=True,
            is_archived=False,
            api_fetched='No'
        )
        db_bet1.set_bet_data(bet1)
        db.session.add(db_bet1)
        
        # Add bet 2
        db_bet2 = Bet(
            user_id=user.id,
            status='live',
            is_active=True,
            is_archived=False,
            api_fetched='No'
        )
        db_bet2.set_bet_data(bet2)
        db.session.add(db_bet2)
        
        db.session.commit()
        
        print("✅ Successfully added 2 live bets!")
        print(f"   1. {bet1['name']} - 7 legs - ${bet1['wager']} to win ${bet1['potential_payout']}")
        print(f"   2. {bet2['name']} - 15 legs - ${bet2['wager']} to win ${bet2['potential_payout']}")

if __name__ == '__main__':
    add_live_bets()
