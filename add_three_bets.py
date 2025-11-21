#!/usr/bin/env python3
"""
Add 3 bets from today's Bills vs Texans game (November 20, 2025)
Based on OCR of screenshots and following the bet addition checklist.
"""

from app import app, db
from models import User, Bet, BetLeg
from datetime import datetime
import json

def add_three_bets():
    """Add the 3 bets from today's Bills vs Texans game"""

    with app.app_context():
        try:
            # Get the user (assuming manishslal is the bettor)
            user = User.query.filter(User.username.ilike('manishslal')).first()
            if not user:
                print("ERROR: manishslal user not found!")
                return

            print(f"Found user: {user.username} (ID: {user.id})")

            # Bet 1: Same Game Parlay (FanDuel)
            bet1_data = {
                "bet_id": "O/0240915/0000075",
                "name": "Khalil Shakir Parlay",
                "type": "Same Game Parlay",
                "betting_site": "FanDuel",
                "bet_date": "2025-11-20",
                "wager": 10.00,
                "odds": "+1034",
                "returns": 113.45,
                "legs": [
                    {
                        "player": "Khalil Shakir",
                        "team": "Buffalo Bills",
                        "stat": "receiving_yards",
                        "target": 60.0,
                        "position": "WR",
                        "sport": "NFL"
                    },
                    {
                        "player": "Khalil Shakir",
                        "team": "Buffalo Bills",
                        "stat": "anytime_touchdown_scorer",
                        "target": 0.0,
                        "position": "WR",
                        "sport": "NFL"
                    },
                    {
                        "player": "Josh Allen",
                        "team": "Buffalo Bills",
                        "stat": "passing_touchdowns",
                        "target": 2.0,
                        "position": "QB",
                        "sport": "NFL"
                    }
                ]
            }

            # Bet 2: Single Bet (FanDuel)
            bet2_data = {
                "bet_id": "O/0240915/0000073",
                "name": "Khalil Shakir Touchdown",
                "type": "Single Bet",
                "betting_site": "FanDuel",
                "bet_date": "2025-11-20",
                "wager": 10.00,
                "odds": "+260",
                "returns": 36.00,
                "legs": [
                    {
                        "player": "Khalil Shakir",
                        "team": "Buffalo Bills",
                        "stat": "anytime_touchdown_scorer",
                        "target": 0.0,
                        "position": "WR",
                        "sport": "NFL"
                    }
                ]
            }

            # Bet 3: Same Game Parlay (FanDuel)
            bet3_data = {
                "bet_id": "O/0240915/0000074",
                "name": "7-Leg Parlay",
                "type": "Same Game Parlay",
                "betting_site": "FanDuel",
                "bet_date": "2025-11-20",
                "wager": 10.00,
                "odds": "+519",
                "returns": 61.99,
                "legs": [
                    {
                        "player": "Davis Mills",
                        "team": "Houston Texans",
                        "stat": "passing_yards",
                        "target": 150.0,
                        "position": "QB",
                        "sport": "NFL"
                    },
                    {
                        "player": "Nico Collins",
                        "team": "Houston Texans",
                        "stat": "receiving_yards",
                        "target": 40.0,
                        "position": "WR",
                        "sport": "NFL"
                    },
                    {
                        "player": "Dalton Schultz",
                        "team": "Houston Texans",
                        "stat": "receiving_yards",
                        "target": 20.0,
                        "position": "TE",
                        "sport": "NFL"
                    },
                    {
                        "player": "James Cook",
                        "team": "Houston Texans",
                        "stat": "rushing_yards",
                        "target": 60.0,
                        "position": "RB",
                        "sport": "NFL"
                    },
                    {
                        "player": "Josh Allen",
                        "team": "Buffalo Bills",
                        "stat": "passing_yards",
                        "target": 175.0,
                        "position": "QB",
                        "sport": "NFL"
                    },
                    {
                        "player": "Dawson Knox",
                        "team": "Buffalo Bills",
                        "stat": "receiving_yards",
                        "target": 15.0,
                        "position": "TE",
                        "sport": "NFL"
                    },
                    {
                        "player": "Khalil Shakir",
                        "team": "Buffalo Bills",
                        "stat": "receiving_yards",
                        "target": 40.0,
                        "position": "WR",
                        "sport": "NFL"
                    }
                ]
            }

            bets_data = [bet1_data, bet2_data, bet3_data]

            for bet_idx, bet_data in enumerate(bets_data, 1):
                print(f"\n{'='*50}")
                print(f"Adding Bet {bet_idx}: {bet_data['name']}")
                print(f"{'='*50}")

                # Check if bet already exists
                existing = Bet.query.filter_by(betting_site_id=bet_data['bet_id']).first()
                if existing:
                    print(f"⚠️  Bet {bet_data['bet_id']} already exists (DB ID: {existing.id}) - skipping")
                    continue

                # Create bet JSON data
                bet_json = {
                    "bet_id": bet_data["bet_id"],
                    "type": bet_data["type"],
                    "parlay_type": "Same Game Parlay" if len(bet_data["legs"]) > 1 else "Single Bet",
                    "sport": "NFL",
                    "sportsbook": bet_data["betting_site"],
                    "wager": bet_data["wager"],
                    "bonus_bets_used": 0,
                    "potential_return": bet_data["returns"],
                    "bet_date": bet_data["bet_date"],
                    "placed_at": f"{bet_data['bet_date']}T18:45:00-05:00",  # Eastern Time
                    "legs": []  # Empty - stored in BetLeg table
                }

                # Create bet
                bet = Bet(user_id=user.id)
                bet.set_bet_data(bet_json)
                bet.betting_site_id = bet_data["bet_id"]
                bet.bet_type = 'parlay' if len(bet_data["legs"]) > 1 else 'single'
                bet.betting_site = bet_data["betting_site"]
                bet.status = 'live'  # Since game is happening now
                bet.is_active = True
                bet.is_archived = False
                bet.api_fetched = 'No'
                bet.wager = bet_data["wager"]
                bet.final_odds = bet_data["odds"]
                bet.potential_winnings = bet_data["returns"]
                bet.bet_date = datetime.strptime(bet_data["bet_date"], '%Y-%m-%d').date()
                bet.total_legs = len(bet_data["legs"])
                bet.legs_pending = len(bet_data["legs"])

                db.session.add(bet)
                db.session.flush()  # Get the ID

                print(f"✅ Created Bet ID {bet.id} in database")
                print(f"   Type: {bet_data['type']}")
                print(f"   Site: {bet_data['betting_site']}")
                print(f"   Wager: ${bet_data['wager']}")
                print(f"   Odds: {bet_data['odds']}")
                print(f"   Returns: ${bet_data['returns']}")

                # Add legs
                print(f"   Adding {len(bet_data['legs'])} legs...")

                for leg_idx, leg_data in enumerate(bet_data["legs"], 1):
                    leg = BetLeg()
                    leg.bet_id = bet.id
                    leg.player_name = leg_data["player"]
                    leg.player_team = leg_data["team"]
                    leg.player_position = leg_data["position"]
                    leg.home_team = "Houston Texans"  # All legs are for this game
                    leg.away_team = "Buffalo Bills"   # All legs are for this game
                    leg.game_date = datetime.strptime(bet_data["bet_date"], '%Y-%m-%d').date()
                    leg.sport = leg_data["sport"]
                    leg.parlay_sport = leg_data["sport"]

                    # Map stat types to database format
                    stat_mapping = {
                        "receiving_yards": "receiving_yards",
                        "anytime_touchdown_scorer": "anytime_touchdown_scorer",
                        "passing_touchdowns": "passing_touchdowns",
                        "passing_yards": "passing_yards",
                        "rushing_yards": "rushing_yards"
                    }
                    leg.bet_type = stat_mapping.get(leg_data["stat"], leg_data["stat"])
                    leg.target_value = leg_data["target"]
                    leg.bet_line_type = 'over'  # All are "over" bets
                    leg.status = 'live'  # Game is live
                    leg.leg_order = leg_idx

                    db.session.add(leg)
                    print(f"     ✅ Leg {leg_idx}: {leg_data['player']} - {leg_data['stat']} over {leg_data['target']}")

                print(f"✅ Bet {bet_idx} completed successfully!")

            db.session.commit()
            print(f"\n🎉 All 3 bets added successfully!")
            print("They are now linked to ESPN API for live tracking of the Bills vs Texans game.")

        except Exception as e:
            print(f"❌ Error adding bets: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    add_three_bets()