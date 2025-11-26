from app import app
from models import db, Player

def fix_gibbs():
    with app.app_context():
        print("Fixing Jahmyr Gibbs data...")
        gibbs = Player.query.filter(Player.player_name.ilike('%Jahmyr Gibbs%')).first()
        if gibbs:
            print(f"Found Gibbs: {gibbs.player_name}, Jersey: {gibbs.jersey_number}, Team: {gibbs.current_team}")
            gibbs.jersey_number = 26
            gibbs.current_team = "Detroit Lions"
            gibbs.team_abbreviation = "DET"
            try:
                db.session.commit()
                print("Successfully updated Gibbs: Jersey=26, Team=Detroit Lions")
            except Exception as e:
                db.session.rollback()
                print(f"Error updating Gibbs: {e}")
        else:
            print("Jahmyr Gibbs not found.")

if __name__ == "__main__":
    fix_gibbs()
