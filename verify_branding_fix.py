from app import app
from models import db, BetLeg, Team, Player



with app.app_context():

    # Check counts
    team_count = Team.query.count()
    leg_count = BetLeg.query.count()
    print(f"\nTotal Teams: {team_count}")
    print(f"Total BetLegs: {leg_count}")

    if team_count > 0:
        print("\n=== Listing First 5 Teams ===")
        teams = Team.query.limit(5).all()
        for t in teams:
            print(f"ID: {t.id}, Name: {t.team_name}, Color: {t.color}")
    
    if leg_count > 0:
        print("\n=== Listing First 5 BetLegs ===")
        legs = BetLeg.query.limit(5).all()
        for l in legs:
            print(f"ID: {l.id}, Player: {l.player_name}, Team: {l.player_team}")
            
    # Check for Mooney again
    print("\n=== Checking for Mooney again ===")
    mooney = BetLeg.query.filter(BetLeg.player_name.ilike('%Mooney%')).first()
    if mooney:
        print(f"Found Mooney: {mooney.player_name}, Team: {mooney.player_team}")
        data = {}
        mooney._add_branding_info(data)
        print(f"Mooney Branding: Color={data.get('team_color')}, Logo={data.get('team_logo')}")
    else:
        print("Mooney not found.")

    # Re-test DET lookup
    print("\n=== Testing Abbreviation Lookup (DET) ===")
    dummy_leg = BetLeg(player_team="DET", sport="NFL")
    data = {}
    dummy_leg._add_branding_info(data)
    print(f"DET Lookup Result: Color={data.get('team_color')}, Logo={data.get('team_logo')}")


