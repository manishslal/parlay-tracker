
from app import app, db
from models import Team, Player

def fix_data():
    with app.app_context():
        print("--- Fixing Missing Data ---")
        
        # 1. Seed Teams
        teams_data = [
            {
                'team_name': 'Golden State Warriors',
                'team_abbr': 'GS',
                'sport': 'NBA',
                'color': '#1D428A',
                'alternate_color': '#FFC72C',
                'logo_url': 'https://a.espncdn.com/i/teamlogos/nba/500/gs.png'
            },
            {
                'team_name': 'Cleveland Cavaliers',
                'team_abbr': 'CLE',
                'sport': 'NBA',
                'color': '#860038',
                'alternate_color': '#FDBB30',
                'logo_url': 'https://a.espncdn.com/i/teamlogos/nba/500/cle.png'
            }
        ]
        
        for t_data in teams_data:
            team = Team.query.filter_by(team_name=t_data['team_name']).first()
            if not team:
                print(f"Creating team: {t_data['team_name']}")
                team = Team(**t_data)
                db.session.add(team)
            else:
                print(f"Updating team: {t_data['team_name']}")
                team.color = t_data['color']
                team.alternate_color = t_data['alternate_color']
                team.logo_url = t_data['logo_url']
                team.team_abbr = t_data['team_abbr']
                team.sport = t_data['sport']
        
        # 2. Update Players
        players_data = [
            {'name': 'Stephen Curry', 'number': 30},
            {'name': 'Evan Mobley', 'number': 4},
            {'name': 'Darius Garland', 'number': 10}
        ]
        
        for p_data in players_data:
            player = Player.query.filter(Player.player_name.ilike(p_data['name'])).first()
            if player:
                print(f"Updating player: {player.player_name} -> Jersey {p_data['number']}")
                player.jersey_number = p_data['number']
            else:
                print(f"Player not found: {p_data['name']}")
        
        db.session.commit()
        print("Data fix complete.")

if __name__ == "__main__":
    fix_data()
