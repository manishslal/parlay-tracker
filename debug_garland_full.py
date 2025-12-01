from app import app
from models import Bet, BetLeg
from services.bet_service import process_parlay_data, calculate_bet_value, fetch_game_details_from_espn

def debug_garland_execution():
    print("=== Debugging Garland Assists Execution ===\n")
    with app.app_context():
        # Get bet 8 (the SGP with Garland)
        bet = Bet.query.get(8)
        if not bet:
            print("Bet 8 not found")
            return
        
        # Find Garland's leg
        garland_leg = None
        for leg in bet.bet_legs_rel:
            if "Garland" in leg.player_name:
                garland_leg = leg
                break
        
        if not garland_leg:
            print("Garland leg not found")
            return
        
        print(f"Leg: {garland_leg.player_name}")
        print(f"  Stat Type: '{garland_leg.stat_type}'")
        print(f"  Home: {garland_leg.home_team}")
        print(f"  Away: {garland_leg.away_team}")
        print(f"  Game Date: {garland_leg.game_date}")
        print(f"  Sport: {garland_leg.sport}")
        
        # Fetch game data
        game_data = fetch_game_details_from_espn(
            game_date=str(garland_leg.game_date),
            away_team=garland_leg.away_team,
            home_team=garland_leg.home_team,
            sport=garland_leg.sport or 'NBA'
        )
        
        if not game_data:
            print("\n❌ No game data fetched")
            return
        
        print(f"\n✅ Game data fetched")
        print(f"  Teams: {game_data.get('teams')}")
        print(f"  Boxscore: {len(game_data.get('boxscore', []))} teams")
        
        # Try to calculate bet value
        leg_dict = {
            'player': garland_leg.player_name,
            'stat': garland_leg.stat_type,
            'target': float(garland_leg.target_value),
        }
        
        print(f"\nCalling calculate_bet_value with:")
        print(f"  player: '{leg_dict['player']}'")
        print(f"  stat: '{leg_dict['stat']}'")
        print(f"  target: {leg_dict['target']}")
        
        result = calculate_bet_value(leg_dict, game_data)
        print(f"\n📊 Result: {result}")
        
        # Now let's process through the full parlay data pipeline
        print("\n=== Testing Full Pipeline ===")
        bet_dict = bet.to_dict_structured()
        processed = process_parlay_data([bet_dict])
        
        if processed:
            for leg in processed[0].get('legs', []):
                if 'Garland' in leg.get('player', ''):
                    print(f"\nProcessed Garland leg:")
                    print(f"  Current: {leg.get('current')}")
                    print(f"  Target: {leg.get('target')}")
                    print(f"  Stat: {leg.get('stat')}")

if __name__ == "__main__":
    debug_garland_execution()
