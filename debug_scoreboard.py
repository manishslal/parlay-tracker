import sys
import os
from app import app, db
from models import Bet, BetLeg, Team
import json

def debug_scoreboard():
    with app.app_context():
        print("\n" + "="*50)
        print("SCOREBOARD DEBUGGER")
        print("="*50 + "\n")
        
        # 1. Inspect Team Cache
        print("--- 1. Team Cache Inspection ---")
        # Trigger cache load
        Team.get_team_by_name_cached("Test")
        cache_size = len(Team._team_cache) if hasattr(Team, '_team_cache') else 0
        print(f"Cache Size: {cache_size} entries")
        
        # Print keys starting with 'los'
        print("Cache keys starting with 'los':")
        if hasattr(Team, '_team_cache'):
            los_keys = [k for k in Team._team_cache.keys() if k.startswith('los')]
            for k in sorted(los_keys):
                t = Team._team_cache[k]
                print(f"  '{k}' -> {t.team_name} ({t.team_abbr})")
        else:
            print("  Cache not initialized!")
            
        print("\n" + "-"*30 + "\n")
        
        # 2. Inspect Bet Legs (Source of Truth)
        print("--- 2. Bet Leg Inspection (Teams starting with 'Los') ---")
        legs = BetLeg.query.filter(
            (BetLeg.home_team.like('Los%')) | (BetLeg.away_team.like('Los%'))
        ).limit(20).all()
        
        if not legs:
            print("No legs found starting with 'Los'. Checking all legs...")
            legs = BetLeg.query.limit(10).all()
            
        seen_teams = set()
        for leg in legs:
            if leg.home_team and leg.home_team.startswith('Los'):
                seen_teams.add(leg.home_team)
            if leg.away_team and leg.away_team.startswith('Los'):
                seen_teams.add(leg.away_team)
                
        print(f"Found {len(seen_teams)} unique 'Los' team names in DB:")
        for team_name in sorted(seen_teams):
            match = Team.get_team_by_name_cached(team_name)
            status = "MATCH" if match else "FAIL"
            abbr = match.team_abbr if match else "N/A"
            fallback = team_name[:3].upper() if not match else "N/A"
            print(f"  '{team_name}' -> {status} (Abbr: {abbr}) [Fallback would be: {fallback}]")
            
            if not match:
                # Debug why it failed
                print(f"    DEBUG: '{team_name.lower()}' not in cache keys.")
                # Check for near matches
                for k in Team._team_cache.keys():
                    if 'lakers' in k and 'lakers' in team_name.lower():
                         print(f"    Did you mean cache key: '{k}'?")
        
        print("\n" + "-"*30 + "\n")

        # 3. Inspect Bet Data JSON (Alternative Source)
        print("--- 3. Bet Data JSON Inspection ---")
        bets = Bet.query.order_by(Bet.id.desc()).limit(5).all()
        for bet in bets:
            if bet.bet_data:
                try:
                    data = json.loads(bet.bet_data)
                    legs = data.get('legs', [])
                    for leg in legs:
                        home = leg.get('home_team')
                        if home and home.startswith('Los'):
                            print(f"  Bet {bet.id} JSON: '{home}'")
                except:
                    pass

if __name__ == "__main__":
    debug_scoreboard()
