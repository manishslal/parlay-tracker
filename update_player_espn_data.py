#!/usr/bin/env python3
"""
Update Players with Team and Jersey Number from ESPN API
Fetches current team and jersey number for all players in the database
"""

import os
import sys
import requests
import time
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    """Get database connection"""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ ERROR: DATABASE_URL not set!")
        sys.exit(1)
    
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    return psycopg2.connect(database_url, cursor_factory=RealDictCursor)

def search_espn_player(player_name, sport):
    """Search for a player on ESPN and return their details."""
    try:
        # Map sport to ESPN API components
        sport_map = {
            'NFL': {'sport': 'football', 'league': 'nfl', 'search': 'nfl'},
            'NBA': {'sport': 'basketball', 'league': 'nba', 'search': 'nba'},
            'MLB': {'sport': 'baseball', 'league': 'mlb', 'search': 'mlb'},
            'NHL': {'sport': 'hockey', 'league': 'nhl', 'search': 'nhl'}
        }
        
        sport_config = sport_map.get(sport)
        if not sport_config:
            return None
            
        sport_type = sport_config['sport']
        league = sport_config['league']
        search_sport = sport_config['search']
        
        # Step 1: Search for player using web search API
        search_url = "https://site.web.api.espn.com/apis/search/v2"
        params = {
            'query': player_name,
            'limit': 5,
            'type': 'player',
            'sport': search_sport
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(search_url, params=params, headers=headers, timeout=5)
        
        if response.status_code != 200:
            return None
            
        data = response.json()
        results = data.get('results', [])
        
        # Find the player type result
        player_id = None
        for result_type in results:
            if result_type.get('type') == 'player':
                contents = result_type.get('contents', [])
                if contents:
                    player = contents[0]  # Take first match
                    
                    # Extract player ID from the web link
                    link = player.get('link', {}).get('web', '')
                    if '/player/' in link and '/id/' in link:
                        # Format: https://www.espn.com/nfl/player/_/id/3139477/patrick-mahomes
                        parts = link.split('/id/')
                        if len(parts) > 1:
                            player_id = parts[1].split('/')[0]
                            break
        
        if not player_id:
            return None
        
        # Step 2: Fetch detailed athlete info from core API
        detail_url = f"https://sports.core.api.espn.com/v2/sports/{sport_type}/leagues/{league}/athletes/{player_id}"
        detail_response = requests.get(detail_url, headers=headers, timeout=5)
        
        if detail_response.status_code != 200:
            return None
            
        athlete_data = detail_response.json()
        jersey = athlete_data.get('jersey')
        
        # Step 3: Fetch team info if available
        team_name = None
        team_abbr = None
        if 'team' in athlete_data and isinstance(athlete_data['team'], dict):
            team_ref = athlete_data['team'].get('$ref')
            if team_ref:
                team_response = requests.get(team_ref, headers=headers, timeout=5)
                if team_response.status_code == 200:
                    team_data = team_response.json()
                    team_name = team_data.get('displayName')
                    team_abbr = team_data.get('abbreviation')
        
        # Get position
        position = None
        if 'position' in athlete_data and isinstance(athlete_data['position'], dict):
            pos_ref = athlete_data['position'].get('$ref')
            if pos_ref:
                pos_response = requests.get(pos_ref, headers=headers, timeout=5)
                if pos_response.status_code == 200:
                    pos_data = pos_response.json()
                    position = pos_data.get('abbreviation')
        
        return {
            'espn_id': player_id,
            'jersey': jersey,
            'team_name': team_name,
            'team_abbr': team_abbr,
            'position': position
        }
        
    except Exception as e:
        print(f"Error searching for {player_name}: {e}")
        return None

def update_player_info(cursor, player_id, info):
    """Update player with ESPN info"""
    cursor.execute("""
        UPDATE players SET
            current_team = COALESCE(%s, current_team),
            team_abbreviation = COALESCE(%s, team_abbreviation),
            jersey_number = COALESCE(%s, jersey_number),
            position = COALESCE(%s, position),
            espn_player_id = COALESCE(%s, espn_player_id),
            last_stats_update = NOW(),
            updated_at = NOW()
        WHERE id = %s
    """, (
        info.get('team_name'),
        info.get('team_abbr'),
        info.get('jersey'),
        info.get('position'),
        info.get('espn_id'),
        player_id
    ))

def main():
    print("=" * 70)
    print("🏈 UPDATING PLAYERS WITH ESPN DATA")
    print("=" * 70)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get all players that need updates
        cursor.execute("""
            SELECT id, player_name, sport, current_team, jersey_number, team_abbreviation
            FROM players
            WHERE espn_player_id IS NULL
            ORDER BY id
        """)
        
        players = cursor.fetchall()
        print(f"\n📋 Found {len(players)} players to update\n")
        
        updated_count = 0
        failed_count = 0
        
        for idx, player in enumerate(players, 1):
            player_id = player['id']
            player_name = player['player_name']
            sport = player['sport']
            
            print(f"[{idx}/{len(players)}] {player_name} ({sport})...")
            
            # Search ESPN
            info = search_espn_player(player_name, sport)
            
            if info:
                print(f"  ✅ Found: {info.get('team_abbr')} #{info.get('jersey')} {info.get('position')}")
                update_player_info(cursor, player_id, info)
                updated_count += 1
                conn.commit()
            else:
                print(f"  ❌ Not found on ESPN")
                failed_count += 1
            
            # Rate limit - be nice to ESPN
            if idx % 10 == 0:
                print(f"\n  💤 Pausing... ({updated_count} updated, {failed_count} failed so far)\n")
                time.sleep(2)
            else:
                time.sleep(0.5)
        
        print("\n" + "=" * 70)
        print("✅ PLAYER UPDATE COMPLETE")
        print("=" * 70)
        print(f"\n📊 Results:")
        print(f"   Updated: {updated_count}")
        print(f"   Failed: {failed_count}")
        print(f"   Total: {len(players)}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()
