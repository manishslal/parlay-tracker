#!/usr/bin/env python3
"""Fix all bet_legs with incomplete home/away team and game_id information."""

import os
import sys
import time
import psycopg2
import requests
from datetime import datetime, timedelta

def fix_all_teams_and_game_ids():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        return False
    
    try:
        conn = psycopg2.connect(database_url, sslmode='require')
        cur = conn.cursor()
        
        print("🔄 Fixing bet_legs with incomplete team/game_id info")
        print("=" * 80)
        
        # Get ALL bet_legs that need fixing
        cur.execute("""
            SELECT id, player_team, sport, game_date
            FROM bet_legs
            WHERE (away_team = '' OR away_team IS NULL OR 
                   home_team = '' OR home_team IS NULL OR
                   game_id = '' OR game_id IS NULL)
              AND player_team IS NOT NULL
              AND game_date IS NOT NULL
            ORDER BY game_date DESC
        """)
        
        legs_to_fix = cur.fetchall()
        total = len(legs_to_fix)
        print(f"Found {total} bet_legs to fix\n")
        
        fixed = 0
        failed = 0
        
        # Cache for game data
        game_cache = {}
        
        for leg_id, team_name, sport, game_date in legs_to_fix:
            cache_key = f"{sport}:{team_name}:{game_date}"
            
            if cache_key in game_cache:
                home_team, away_team, game_id = game_cache[cache_key]
            else:
                # Get team ID
                cur.execute('SELECT espn_team_id FROM teams WHERE team_name = %s AND sport = %s', (team_name, sport))
                result = cur.fetchone()
                if not result:
                    print(f"  ❌ {leg_id}: Team {team_name} not found in teams table")
                    failed += 1
                    continue
                
                team_id = result[0]
                
                # Fetch schedule
                year = game_date.year
                if sport == 'NFL':
                    url = f'https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}/schedule?season={year}'
                elif sport == 'NBA':
                    url = f'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/schedule?season={year}'
                else:
                    failed += 1
                    continue
                
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(url, headers=headers, timeout=10)
                time.sleep(0.3)
                
                if response.status_code != 200:
                    print(f"  ❌ {leg_id}: Failed to fetch schedule for {team_name}")
                    failed += 1
                    continue
                
                data = response.json()
                events = data.get('events', [])
                
                home_team = None
                away_team = None
                game_id = None
                
                # Find game on this date
                for event in events:
                    event_date_str = event.get('date', '')
                    if event_date_str:
                        event_dt = datetime.fromisoformat(event_date_str.replace('Z', '+00:00'))
                        event_date_eastern = (event_dt - timedelta(hours=5)).date()
                        
                        if event_date_eastern == game_date:
                            # Found the game!
                            competitions = event.get('competitions', [])
                            if competitions:
                                comp = competitions[0]
                                competitors = comp.get('competitors', [])
                                game_id = event.get('id')
                                
                                for competitor in competitors:
                                    team = competitor.get('team', {})
                                    team_abbr = team.get('abbreviation', '')
                                    is_home = competitor.get('homeAway') == 'home'
                                    
                                    if is_home:
                                        home_team = team_abbr
                                    else:
                                        away_team = team_abbr
                                
                                break
                
                game_cache[cache_key] = (home_team, away_team, game_id)
            
            if home_team and away_team and game_id:
                cur.execute("""
                    UPDATE bet_legs
                    SET home_team = %s, away_team = %s, game_id = %s, updated_at = NOW()
                    WHERE id = %s
                """, (home_team, away_team, game_id, leg_id))
                conn.commit()
                fixed += 1
                if fixed % 20 == 0:
                    print(f"  ✅ Fixed {fixed}/{total} bet_legs...")
            else:
                failed += 1
        
        print()
        print("=" * 80)
        print(f"✅ Fixed: {fixed}")
        print(f"❌ Failed: {failed}")
        print("=" * 80)
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_all_teams_and_game_ids()
    sys.exit(0 if success else 1)
