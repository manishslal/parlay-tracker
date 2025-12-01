from app import app, db
from models import BetLeg
from services.bet_service import fetch_game_details_from_espn, calculate_bet_value

def update_garland_leg():
    print("=== Updating Garland Leg ===\n")
    with app.app_context():
        # Find Garland's leg  
        leg = BetLeg.query.filter(
            BetLeg.bet_id == 8,
            BetLeg.player_name.like('%Garland%')
        ).first()
        
        if not leg:
            print("Garland leg not found")
            return
        
        print(f"Current:")
        print(f"  Achieved: {leg.achieved_value}")
        print(f"  Game Status: {leg.game_status}")
        
        # Fetch game data
        game_data = fetch_game_details_from_espn(
            game_date=str(leg.game_date),
            away_team=leg.away_team,
            home_team=leg.home_team,
            sport='NBA'
        )
        
        if not game_data:
            print("\n❌ No game data found")
            return
        
        print(f"\n✅ Game data found")
        print(f"  Status: {game_data.get('statusTypeName')}")
        print(f"  Score: {game_data.get('score')}")
        
        # Calculate value
        leg_dict = {
            'player': leg.player_name,
            'stat': leg.stat_type,
            'target': float(leg.target_value),
        }
        
        result = calculate_bet_value(leg_dict, game_data)
        print(f"  Calculated assists: {result}")
        
        # Update the leg
        leg.achieved_value = result
        leg.game_status = game_data.get('statusTypeName')
        leg.home_score = game_data.get('score', {}).get('home', 0)
        leg.away_score = game_data.get('score', {}).get('away', 0)
        
        db.session.commit()
        
        print(f"\n✅ Updated:")
        print(f"  Achieved: {leg.achieved_value}")
        print(f"  Game Status: {leg.game_status}")

if __name__ == "__main__":
    update_garland_leg()
