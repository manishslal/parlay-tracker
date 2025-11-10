#!/usr/bin/env python3
"""
Add 3 bets for manishslal (Nov 9, 2025)
- Bet 1: DraftKings 8-Pick Parlay (8 moneyline bets)
- Bet 2: Dabble 2-Pick Parlay (2 player props)
- Bet 3: FanDuel 12-Leg Game Parlay (5 SGPs with passing yards)

Viewer: etoteja
"""

from app import app, db
from models import User, Bet, BetLeg
from datetime import datetime

def add_manishslal_bets():
    with app.app_context():
        # Get or create users
        manish = User.query.filter_by(username='manishslal').first()
        if not manish:
            print("❌ User 'manishslal' not found. Please create user first.")
            return
        
        etoteja = User.query.filter_by(username='etoteja').first()
        if not etoteja:
            print("❌ User 'etoteja' not found. Please create user first.")
            return
        
        print(f"✅ Found users: {manish.username}, {etoteja.username}")
        
        # ========================================
        # BET 1: DraftKings 8-Pick Parlay
        # ========================================
        bet1_data = {
            "bet_id": "DK638983074399290190",
            "name": "8 Pick Parlay",
            "type": "Parlay",
            "betting_site": "DraftKings",
            "bet_date": "2025-11-09",
            "wager": "10.00",
            "odds": "+1487",
            "returns": "148.70",  # $158.70 - $10.00
            "legs": [
                {
                    "away": "New England Patriots",
                    "home": "Tampa Bay Buccaneers",
                    "game_date": "2025-11-10",
                    "stat": "moneyline",
                    "target": 0,
                    "team": "Tampa Bay Buccaneers",
                    "sport": "NFL"
                },
                {
                    "away": "Buffalo Bills",
                    "home": "Miami Dolphins",
                    "game_date": "2025-11-10",
                    "stat": "moneyline",
                    "target": 0,
                    "team": "Buffalo Bills",
                    "sport": "NFL"
                },
                {
                    "away": "Baltimore Ravens",
                    "home": "Minnesota Vikings",
                    "game_date": "2025-11-10",
                    "stat": "moneyline",
                    "target": 0,
                    "team": "Baltimore Ravens",
                    "sport": "NFL"
                },
                {
                    "away": "New York Giants",
                    "home": "Chicago Bears",
                    "game_date": "2025-11-10",
                    "stat": "moneyline",
                    "target": 0,
                    "team": "Chicago Bears",
                    "sport": "NFL"
                },
                {
                    "away": "Detroit Lions",
                    "home": "Washington Commanders",
                    "game_date": "2025-11-10",
                    "stat": "moneyline",
                    "target": 0,
                    "team": "Detroit Lions",
                    "sport": "NFL"
                },
                {
                    "away": "Arizona Cardinals",
                    "home": "Seattle Seahawks",
                    "game_date": "2025-11-10",
                    "stat": "moneyline",
                    "target": 0,
                    "team": "Seattle Seahawks",
                    "sport": "NFL"
                },
                {
                    "away": "Los Angeles Rams",
                    "home": "San Francisco 49ers",
                    "game_date": "2025-11-10",
                    "stat": "moneyline",
                    "target": 0,
                    "team": "Los Angeles Rams",
                    "sport": "NFL"
                },
                {
                    "away": "New Orleans Saints",
                    "home": "Carolina Panthers",
                    "game_date": "2025-11-10",
                    "stat": "moneyline",
                    "target": 0,
                    "team": "Carolina Panthers",
                    "sport": "NFL"
                }
            ]
        }
        
        # ========================================
        # BET 2: Dabble 2-Pick Parlay
        # ========================================
        bet2_data = {
            "bet_id": "701a63c1-4917-4cd6-834b-5852d71c9f79",
            "name": "2 Picks (All-In)",
            "type": "Parlay",
            "betting_site": "Dabble",
            "bet_date": "2025-11-09",
            "wager": "20.00",
            "odds": "+200",
            "returns": "40.00",  # $60.00 - $20.00
            "legs": [
                {
                    "away": "Cleveland Browns",
                    "home": "New York Jets",
                    "game_date": "2025-11-10",
                    "stat": "rushing_yards",
                    "target": 81.5,
                    "team": "Cleveland Browns",
                    "player": "Quinshon Judkins",
                    "position": "RB",
                    "sport": "NFL"
                },
                {
                    "away": "New York Giants",
                    "home": "Chicago Bears",
                    "game_date": "2025-11-10",
                    "stat": "receiving_yards",
                    "target": 51.5,
                    "team": "Chicago Bears",
                    "player": "Rome Odunze",
                    "position": "WR",
                    "sport": "NFL"
                }
            ]
        }
        
        # ========================================
        # BET 3: FanDuel 12-Leg Game Parlay
        # ========================================
        bet3_data = {
            "bet_id": "O/0240915/0000069",
            "name": "12 leg Game Game Parlay+",
            "type": "Parlay",
            "betting_site": "FanDuel",
            "bet_date": "2025-11-09",
            "wager": "10.00",
            "odds": "+745",
            "returns": "74.58",  # $84.58 - $10.00
            "legs": [
                # SGP 1: Jacksonville Jaguars @ Houston Texans
                {
                    "away": "Jacksonville Jaguars",
                    "home": "Houston Texans",
                    "game_date": "2025-11-10",
                    "stat": "passing_yards",
                    "target": 150.5,
                    "team": "Houston Texans",
                    "player": "Davis Mills",
                    "position": "QB",
                    "sport": "NFL"
                },
                {
                    "away": "Jacksonville Jaguars",
                    "home": "Houston Texans",
                    "game_date": "2025-11-10",
                    "stat": "passing_yards",
                    "target": 150.5,
                    "team": "Jacksonville Jaguars",
                    "player": "Trevor Lawrence",
                    "position": "QB",
                    "sport": "NFL"
                },
                # SGP 2: New York Giants @ Chicago Bears
                {
                    "away": "New York Giants",
                    "home": "Chicago Bears",
                    "game_date": "2025-11-10",
                    "stat": "passing_yards",
                    "target": 150.5,
                    "team": "Chicago Bears",
                    "player": "Caleb Williams",
                    "position": "QB",
                    "sport": "NFL"
                },
                {
                    "away": "New York Giants",
                    "home": "Chicago Bears",
                    "game_date": "2025-11-10",
                    "stat": "passing_yards",
                    "target": 150.5,
                    "team": "New York Giants",
                    "player": "Jaxson Dart",
                    "position": "QB",
                    "sport": "NFL"
                },
                # SGP 3: Baltimore Ravens @ Minnesota Vikings
                {
                    "away": "Baltimore Ravens",
                    "home": "Minnesota Vikings",
                    "game_date": "2025-11-10",
                    "stat": "passing_yards",
                    "target": 150.5,
                    "team": "Minnesota Vikings",
                    "player": "J.J. McCarthy",
                    "position": "QB",
                    "sport": "NFL"
                },
                {
                    "away": "Baltimore Ravens",
                    "home": "Minnesota Vikings",
                    "game_date": "2025-11-10",
                    "stat": "passing_yards",
                    "target": 150.5,
                    "team": "Baltimore Ravens",
                    "player": "Lamar Jackson",
                    "position": "QB",
                    "sport": "NFL"
                },
                # SGP 4: New Orleans Saints @ Carolina Panthers
                {
                    "away": "New Orleans Saints",
                    "home": "Carolina Panthers",
                    "game_date": "2025-11-10",
                    "stat": "passing_yards",
                    "target": 125.5,
                    "team": "Carolina Panthers",
                    "player": "Bryce Young",
                    "position": "QB",
                    "sport": "NFL"
                },
                {
                    "away": "New Orleans Saints",
                    "home": "Carolina Panthers",
                    "game_date": "2025-11-10",
                    "stat": "passing_yards",
                    "target": 125.5,
                    "team": "New Orleans Saints",
                    "player": "Tyler Shough",
                    "position": "QB",
                    "sport": "NFL"
                },
                # SGP 5: New England Patriots @ Tampa Bay Buccaneers
                {
                    "away": "New England Patriots",
                    "home": "Tampa Bay Buccaneers",
                    "game_date": "2025-11-10",
                    "stat": "passing_yards",
                    "target": 175.5,
                    "team": "Tampa Bay Buccaneers",
                    "player": "Baker Mayfield",
                    "position": "QB",
                    "sport": "NFL"
                },
                {
                    "away": "New England Patriots",
                    "home": "Tampa Bay Buccaneers",
                    "game_date": "2025-11-10",
                    "stat": "passing_yards",
                    "target": 175.5,
                    "team": "New England Patriots",
                    "player": "Drake Maye",
                    "position": "QB",
                    "sport": "NFL"
                },
                # Additional legs from image
                {
                    "away": "New England Patriots",
                    "home": "Tampa Bay Buccaneers",
                    "game_date": "2025-11-10",
                    "stat": "passing_yards",
                    "target": 175.5,
                    "team": "Tampa Bay Buccaneers",
                    "player": "Josh Allen",
                    "position": "QB",
                    "sport": "NFL"
                },
                {
                    "away": "Buffalo Bills",
                    "home": "Miami Dolphins",
                    "game_date": "2025-11-10",
                    "stat": "passing_yards",
                    "target": 125.5,
                    "team": "Miami Dolphins",
                    "player": "Dillon Gabriel",
                    "position": "QB",
                    "sport": "NFL"
                }
            ]
        }
        
        # Insert bets
        bets_to_add = [
            (bet1_data, "DraftKings 8-Pick Parlay"),
            (bet2_data, "Dabble 2-Pick Parlay"),
            (bet3_data, "FanDuel 12-Leg Parlay")
        ]
        
        for bet_data, bet_name in bets_to_add:
            print(f"\n{'='*60}")
            print(f"Adding: {bet_name}")
            print(f"{'='*60}")
            
            # Create bet
            bet = Bet(user_id=manish.id)
            bet.set_bet_data(bet_data)
            
            db.session.add(bet)
            db.session.flush()  # Get bet.id
            
            # Add users (primary bettor + viewer)
            bet.add_user(manish, is_primary=True)
            bet.add_user(etoteja, is_primary=False)
            
            # Add legs
            for i, leg_data in enumerate(bet_data['legs'], 1):
                leg = BetLeg(
                    bet_id=bet.id,
                    player_name=leg_data.get('player', leg_data.get('team', '')),
                    player_team=leg_data.get('team', ''),
                    player_position=leg_data.get('position', ''),
                    home_team=leg_data['home'],
                    away_team=leg_data['away'],
                    game_date=datetime.strptime(leg_data['game_date'], '%Y-%m-%d').date(),
                    bet_type=leg_data['stat'],
                    target_value=leg_data['target'],
                    sport=leg_data.get('sport', 'NFL'),
                    leg_order=i
                )
                db.session.add(leg)
            
            print(f"✅ Added: {bet_data['name']}")
            print(f"   Bet ID: {bet_data['bet_id']}")
            print(f"   Legs: {len(bet_data['legs'])}")
            print(f"   Wager: ${bet_data['wager']}")
            print(f"   Potential Return: ${bet_data['returns']}")
        
        # Commit all
        db.session.commit()
        
        print(f"\n{'='*60}")
        print("✅ Successfully added all 3 bets for manishslal!")
        print(f"   Primary Bettor: {manish.username}")
        print(f"   Viewer: {etoteja.username}")
        print(f"{'='*60}")

if __name__ == '__main__':
    add_manishslal_bets()
