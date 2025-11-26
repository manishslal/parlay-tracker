from app import app
from models import db, Player, Team, BetLeg

def verify_data():
    with app.app_context():
        print("=== Checking Jahmyr Gibbs ===")
        # Check Player record
        gibbs = Player.query.filter(Player.player_name.ilike('%Jahmyr Gibbs%')).first()
        if gibbs:
            print(f"Player Record Found: ID={gibbs.id}, Name={gibbs.player_name}, Jersey={gibbs.jersey_number}, Team={gibbs.current_team}")
        else:
            print("Player Record NOT Found for Jahmyr Gibbs.")

        # Check BetLegs for Gibbs
        legs = BetLeg.query.filter(BetLeg.player_name.ilike('%Jahmyr Gibbs%')).all()
        print(f"Found {len(legs)} BetLegs for Jahmyr Gibbs.")
        for leg in legs:
            print(f"  Leg ID: {leg.id}, Player ID: {leg.player_id}, Team: {leg.player_team}")
            # Test branding logic
            data = {}
            leg._add_branding_info(data)
            print(f"  -> Branding: Jersey={data.get('player_jersey_number')}, Logo={data.get('team_logo')}")

        print("\n=== Checking Team Colors ===")
        teams = Team.query.all()
        missing_colors = []
        invalid_format = []
        for team in teams:
            # Check for missing
            if not team.color or not team.alternate_color:
                missing_colors.append(f"{team.team_name} (ID: {team.id}) - Color: {team.color}, Alt: {team.alternate_color}")
                continue
            
            # Check for format (must start with #)
            # Note: The code fix I made handles missing # dynamically, but the data should ideally have it.
            if not team.color.strip().startswith('#') or not team.alternate_color.strip().startswith('#'):
                 invalid_format.append(f"{team.team_name} (ID: {team.id}) - Color: {team.color}, Alt: {team.alternate_color}")
        
        if missing_colors:
            print(f"Found {len(missing_colors)} teams with missing colors:")
            for m in missing_colors:
                print(f"  - {m}")
        else:
            print("All teams have populated colors.")

        if invalid_format:
            print(f"\nFound {len(invalid_format)} teams with invalid hex format (missing #):")
            for m in invalid_format:
                print(f"  - {m}")
        else:
            print("All teams have valid hex format (starting with #).")

if __name__ == "__main__":
    verify_data()
