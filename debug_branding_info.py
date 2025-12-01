
import os
import sys
from app import app, db
from models import BetLeg, Player, Team

def debug_branding():
    with app.app_context():
        print("--- Debugging Branding Info ---")
        
        # Get the most recent 5 bet legs
        legs = BetLeg.query.order_by(BetLeg.created_at.desc()).limit(5).all()
        
        if not legs:
            print("No bet legs found.")
            return

        for leg in legs:
            print(f"\nLeg ID: {leg.id}")
            print(f"  Player Name: {leg.player_name}")
            print(f"  Player ID (in leg): {leg.player_id}")
            print(f"  Team: {leg.player_team}")
            print(f"  Sport: {leg.sport}")
            
            # Call to_dict which triggers _add_branding_info
            data = leg.to_dict()
            
            print("  -> Branding Info from to_dict():")
            print(f"     player_jersey_number: {data.get('player_jersey_number')}")
            print(f"     team_logo: {data.get('team_logo')}")
            print(f"     team_color: {data.get('team_color')}")
            print(f"     jersey_primary_color: {data.get('jersey_primary_color')}")
            
            # Verify Player lookup manually
            if leg.player_id:
                player = Player.query.get(leg.player_id)
                print(f"  -> Manual Player Lookup (ID {leg.player_id}): {player.player_name if player else 'Not Found'}")
                if player:
                    print(f"     Jersey: {player.jersey_number}")
            else:
                print("  -> No Player ID in leg. Trying name lookup...")
                player = Player.query.filter(Player.player_name.ilike(leg.player_name)).first()
                print(f"     Found by name? {player.player_name if player else 'No'}")
                if player:
                     print(f"     Jersey: {player.jersey_number}")

            # Verify Team lookup manually
            if leg.player_team:
                team = Team.query.filter(Team.team_name.ilike(leg.player_team)).first()
                if not team:
                     team = Team.query.filter(Team.team_abbr.ilike(leg.player_team)).first()
                
                print(f"  -> Manual Team Lookup ({leg.player_team}): {team.team_name if team else 'Not Found'}")
                if team:
                    print(f"     Logo: {team.logo_url}")
                    print(f"     Color: {team.color}")

if __name__ == "__main__":
    debug_branding()
