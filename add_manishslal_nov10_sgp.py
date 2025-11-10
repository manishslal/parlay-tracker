"""
Add 8-Pick SGP for manishslal (Nov 10, 2025)
PHI @ GB - Tonight's game at 8:15 PM

Following all lessons learned:
- Use to_dict_structured() for proper leg handling
- Store team CODES (PHI, GB) not full names
- All targets as whole numbers (180, 50, 40, etc.)
- Proper sport codes (NFL)
- Connect to ESPN API with correct game date
- Add both primary bettor and viewer
"""

from app import app, db
from models import User, Bet, BetLeg
from datetime import datetime
import json

def add_nov10_sgp():
    """Add the 8-Pick SGP for manishslal"""
    
    with app.app_context():
        try:
            # Get users
            manishslal = User.query.filter(User.username.ilike('manishslal')).first()
            etoteja = User.query.filter(User.username.ilike('etoteja')).first()
            
            if not manishslal:
                print("ERROR: manishslal user not found!")
                return
            if not etoteja:
                print("ERROR: etoteja user not found!")
                return
            
            print(f"Users found: manishslal (ID: {manishslal.id}), etoteja (ID: {etoteja.id})")
            
            # Bet details
            bet_id = "DK638984135338309629"
            bet_date = "2025-11-10"
            game_date = "2025-11-10"  # Today's game
            wager = 20.00
            potential_return = 96.80
            odds = 384
            
            # Check if bet already exists
            existing = Bet.query.filter_by(bet_id=bet_id).first()
            if existing:
                print(f"Bet {bet_id} already exists (DB ID: {existing.id})!")
                return
            
            # Create bet_data JSON (minimal, legs stored in BetLeg table)
            bet_data = {
                "bet_id": bet_id,
                "type": "SGP",
                "parlay_type": "Same Game Parlay",
                "sport": "NFL",
                "sportsbook": "PrizePicks",
                "wager": wager,
                "bonus_bets_used": 0,
                "potential_return": potential_return,
                "bet_date": bet_date,
                "placed_at": "2025-11-10T18:18:53-05:00",
                "legs": []  # Empty - stored in BetLeg table
            }
            
            # Create bet
            bet = Bet(user_id=manishslal.id)
            bet.set_bet_data(bet_data)
            bet.bet_id = bet_id
            bet.bet_type = 'SGP'
            bet.betting_site = 'PrizePicks'
            bet.status = 'pending'
            bet.is_active = True
            bet.is_archived = False
            bet.api_fetched = 'No'
            bet.wager = wager
            bet.final_odds = odds
            bet.potential_winnings = potential_return
            bet.bet_date = bet_date
            bet.total_legs = 8
            bet.legs_pending = 8
            
            db.session.add(bet)
            db.session.flush()  # Get the ID
            
            print(f"\n✅ Created Bet ID {bet.id} in database")
            
            # Add users to the bet
            bet.add_user(manishslal, is_primary=True)
            print(f"   Added manishslal as primary bettor")
            
            bet.add_user(etoteja, is_primary=False)
            print(f"   Added etoteja as viewer")
            
            # Define all legs - CRITICAL: Use team CODES (PHI, GB), not full names!
            legs = [
                {
                    "player_name": "Jordan Love",
                    "team": "GB",
                    "position": "QB",
                    "stat": "passing_yards",
                    "target": 180,
                    "away": "PHI",
                    "home": "GB",
                    "sport": "NFL"
                },
                {
                    "player_name": "Saquon Barkley",
                    "team": "PHI",
                    "position": "RB",
                    "stat": "rushing_yards",
                    "target": 50,
                    "away": "PHI",
                    "home": "GB",
                    "sport": "NFL"
                },
                {
                    "player_name": "Josh Jacobs",
                    "team": "GB",
                    "position": "RB",
                    "stat": "rushing_yards",
                    "target": 40,
                    "away": "PHI",
                    "home": "GB",
                    "sport": "NFL"
                },
                {
                    "player_name": "Jalen Hurts",
                    "team": "PHI",
                    "position": "QB",
                    "stat": "passing_yards",
                    "target": 150,
                    "away": "PHI",
                    "home": "GB",
                    "sport": "NFL"
                },
                {
                    "player_name": "A.J. Brown",
                    "team": "PHI",
                    "position": "WR",
                    "stat": "receiving_yards",
                    "target": 25,
                    "away": "PHI",
                    "home": "GB",
                    "sport": "NFL"
                },
                {
                    "player_name": "DeVonta Smith",
                    "team": "PHI",
                    "position": "WR",
                    "stat": "receiving_yards",
                    "target": 25,
                    "away": "PHI",
                    "home": "GB",
                    "sport": "NFL"
                },
                {
                    "player_name": "Romeo Doubs",
                    "team": "GB",
                    "position": "WR",
                    "stat": "receiving_yards",
                    "target": 25,
                    "away": "PHI",
                    "home": "GB",
                    "sport": "NFL"
                },
                {
                    "player_name": "Christian Watson",
                    "team": "GB",
                    "position": "WR",
                    "stat": "receiving_yards",
                    "target": 25,
                    "away": "PHI",
                    "home": "GB",
                    "sport": "NFL"
                }
            ]
            
            print(f"\n📋 Adding {len(legs)} legs to bet...")
            
            # Insert each leg
            for idx, leg_data in enumerate(legs, 1):
                leg = BetLeg()
                leg.bet_id = bet.id
                leg.player_name = leg_data['player_name']
                leg.player_team = leg_data['team']
                leg.player_position = leg_data['position']
                leg.home_team = leg_data['home']
                leg.away_team = leg_data['away']
                leg.game_date = datetime.strptime(game_date, '%Y-%m-%d').date()
                leg.sport = leg_data['sport']
                leg.parlay_sport = leg_data['sport']
                leg.bet_type = leg_data['stat']
                leg.target_value = leg_data['target']
                leg.bet_line_type = 'over'
                leg.status = 'pending'
                leg.leg_order = idx
                
                db.session.add(leg)
                print(f"   ✅ Leg {idx}: {leg_data['player_name']} {leg_data['target']}+ {leg_data['stat']}")
            
            db.session.commit()
            
            print(f"\n🎉 SUCCESS!")
            print(f"   Bet ID: {bet_id}")
            print(f"   Database ID: {bet.id}")
            print(f"   Primary Bettor: manishslal")
            print(f"   Viewer: etoteja")
            print(f"   Total Legs: 8")
            print(f"   Game: PHI @ GB")
            print(f"   Wager: ${wager}")
            print(f"   To Win: ${potential_return}")
            print(f"   Odds: +{odds}")
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            raise

if __name__ == "__main__":
    add_nov10_sgp()
