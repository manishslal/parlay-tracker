#!/usr/bin/env python3
"""
Script to populate teams table with NFL and NBA teams from ESPN API.
Fetches team details, standings, and records from ESPN.
"""

import psycopg2
import os
import sys
import requests
import time
from datetime import datetime

# ESPN API endpoints
NFL_TEAMS_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams"
NBA_TEAMS_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams"
NFL_STANDINGS_URL = "https://site.api.espn.com/apis/v2/sports/football/nfl/standings"
NBA_STANDINGS_URL = "https://site.api.espn.com/apis/v2/sports/basketball/nba/standings"

def fetch_espn_data(url, description):
    """Fetch data from ESPN API with error handling."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        print(f"  Fetching {description}...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        time.sleep(0.5)  # Rate limiting
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  ⚠️  Failed to fetch {description}: {e}")
        return None

def extract_team_info(team_data, sport):
    """Extract team information from ESPN team data."""
    team = team_data.get('team', {})
    
    # Basic info
    team_info = {
        'team_name': team.get('displayName', ''),
        'team_name_short': team.get('shortDisplayName', ''),
        'team_abbr': team.get('abbreviation', ''),
        'espn_team_id': team.get('id', ''),
        'sport': sport,
        'location': team.get('location', ''),
        'nickname': team.get('name', ''),
        'is_active': True
    }
    
    # Logos
    logos = team.get('logos', [])
    if logos:
        team_info['logo_url'] = logos[0].get('href', '')
    
    # Colors
    team_info['color'] = team.get('color', '')
    team_info['alternate_color'] = team.get('alternateColor', '')
    
    # Record
    record = team.get('record', {})
    if record:
        items = record.get('items', [])
        for item in items:
            if item.get('type') == 'total':
                stats = item.get('stats', [])
                for stat in stats:
                    stat_name = stat.get('name')
                    stat_value = stat.get('value')
                    
                    if stat_name == 'gamesPlayed':
                        team_info['games_played'] = int(stat_value)
                    elif stat_name == 'wins':
                        team_info['wins'] = int(stat_value)
                    elif stat_name == 'losses':
                        team_info['losses'] = int(stat_value)
                    elif stat_name == 'ties':
                        team_info['ties'] = int(stat_value)
                    elif stat_name == 'winPercent':
                        team_info['win_percentage'] = float(stat_value)
    
    # Standings
    standings = team.get('standingSummary', '')
    if standings:
        # Extract division/conference rank if available
        parts = standings.split(',')
        for part in parts:
            part = part.strip().lower()
            if 'in division' in part or 'in conference' in part:
                try:
                    rank = int(part.split()[0].replace('st', '').replace('nd', '').replace('rd', '').replace('th', ''))
                    if 'division' in part:
                        team_info['division_rank'] = rank
                    elif 'conference' in part:
                        team_info['conference_rank'] = rank
                except:
                    pass
    
    # League/Conference/Division
    groups = team.get('groups', {})
    if groups:
        team_info['league'] = groups.get('name', '')
        parent = groups.get('parent', {})
        if parent:
            team_info['conference'] = parent.get('name', '')
            grandparent = parent.get('parent', {})
            if grandparent:
                team_info['division'] = grandparent.get('name', '')
    
    # Next event
    next_event = team.get('nextEvent', [])
    if next_event and len(next_event) > 0:
        event_date = next_event[0].get('date')
        if event_date:
            try:
                team_info['next_game_date'] = datetime.fromisoformat(event_date.replace('Z', '+00:00')).date()
            except:
                pass
    
    return team_info

def populate_teams(conn, sport, teams_url):
    """Populate teams for a specific sport."""
    print(f"\n{'=' * 80}")
    print(f"Populating {sport.upper()} teams")
    print(f"{'=' * 80}")
    
    # Fetch teams data
    data = fetch_espn_data(teams_url, f"{sport.upper()} teams")
    if not data:
        print(f"  ❌ Failed to fetch {sport.upper()} teams")
        return 0
    
    sports_data = data.get('sports', [])
    if not sports_data:
        print(f"  ❌ No sports data found")
        return 0
    
    leagues = sports_data[0].get('leagues', [])
    if not leagues:
        print(f"  ❌ No leagues found")
        return 0
    
    all_teams = leagues[0].get('teams', [])
    print(f"  Found {len(all_teams)} teams")
    
    cur = conn.cursor()
    inserted_count = 0
    updated_count = 0
    
    for team_data in all_teams:
        try:
            team_info = extract_team_info(team_data, sport)
            
            if not team_info.get('team_name') or not team_info.get('team_abbr'):
                print(f"  ⚠️  Skipping team with incomplete data")
                continue
            
            # Check if team already exists (by ESPN ID and sport to avoid cross-sport matches)
            cur.execute("""
                SELECT id FROM teams 
                WHERE (espn_team_id = %s AND sport = %s) 
                   OR (team_abbr = %s AND sport = %s)
            """, (team_info['espn_team_id'], sport, team_info['team_abbr'], sport))
            
            existing = cur.fetchone()
            
            if existing:
                # Update existing team
                cur.execute("""
                    UPDATE teams SET
                        team_name = %s,
                        team_name_short = %s,
                        team_abbr = %s,
                        espn_team_id = %s,
                        sport = %s,
                        league = %s,
                        conference = %s,
                        division = %s,
                        games_played = %s,
                        wins = %s,
                        losses = %s,
                        ties = %s,
                        win_percentage = %s,
                        division_rank = %s,
                        conference_rank = %s,
                        location = %s,
                        nickname = %s,
                        logo_url = %s,
                        color = %s,
                        alternate_color = %s,
                        is_active = %s,
                        next_game_date = %s,
                        last_stats_update = %s,
                        updated_at = %s
                    WHERE id = %s
                """, (
                    team_info['team_name'],
                    team_info['team_name_short'],
                    team_info['team_abbr'],
                    team_info['espn_team_id'],
                    team_info['sport'],
                    team_info.get('league'),
                    team_info.get('conference'),
                    team_info.get('division'),
                    team_info.get('games_played', 0),
                    team_info.get('wins', 0),
                    team_info.get('losses', 0),
                    team_info.get('ties', 0),
                    team_info.get('win_percentage'),
                    team_info.get('division_rank'),
                    team_info.get('conference_rank'),
                    team_info.get('location'),
                    team_info.get('nickname'),
                    team_info.get('logo_url'),
                    team_info.get('color'),
                    team_info.get('alternate_color'),
                    team_info.get('is_active', True),
                    team_info.get('next_game_date'),
                    datetime.utcnow(),
                    datetime.utcnow(),
                    existing[0]
                ))
                updated_count += 1
                print(f"  ✅ Updated: {team_info['team_name']} ({team_info['team_abbr']})")
            else:
                # Insert new team
                cur.execute("""
                    INSERT INTO teams (
                        team_name, team_name_short, team_abbr, espn_team_id,
                        sport, league, conference, division,
                        games_played, wins, losses, ties, win_percentage,
                        division_rank, conference_rank,
                        location, nickname, logo_url, color, alternate_color,
                        is_active, next_game_date, last_stats_update,
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    team_info['team_name'],
                    team_info['team_name_short'],
                    team_info['team_abbr'],
                    team_info['espn_team_id'],
                    team_info['sport'],
                    team_info.get('league'),
                    team_info.get('conference'),
                    team_info.get('division'),
                    team_info.get('games_played', 0),
                    team_info.get('wins', 0),
                    team_info.get('losses', 0),
                    team_info.get('ties', 0),
                    team_info.get('win_percentage'),
                    team_info.get('division_rank'),
                    team_info.get('conference_rank'),
                    team_info.get('location'),
                    team_info.get('nickname'),
                    team_info.get('logo_url'),
                    team_info.get('color'),
                    team_info.get('alternate_color'),
                    team_info.get('is_active', True),
                    team_info.get('next_game_date'),
                    datetime.utcnow(),
                    datetime.utcnow(),
                    datetime.utcnow()
                ))
                inserted_count += 1
                print(f"  ✅ Inserted: {team_info['team_name']} ({team_info['team_abbr']})")
            
            conn.commit()
            
        except Exception as e:
            print(f"  ❌ Error processing team: {e}")
            conn.rollback()
            continue
    
    cur.close()
    
    print(f"\n  Summary: {inserted_count} inserted, {updated_count} updated")
    return inserted_count + updated_count

def main():
    """Main function to populate teams."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    try:
        print("Connecting to database...")
        conn = psycopg2.connect(database_url, sslmode='require')
        
        # Populate NFL teams
        nfl_count = populate_teams(conn, 'NFL', NFL_TEAMS_URL)
        
        # Populate NBA teams
        nba_count = populate_teams(conn, 'NBA', NBA_TEAMS_URL)
        
        # Show summary
        cur = conn.cursor()
        cur.execute("""
            SELECT sport, COUNT(*) as count
            FROM teams
            GROUP BY sport
            ORDER BY sport
        """)
        
        print(f"\n{'=' * 80}")
        print("Final Team Counts:")
        print(f"{'=' * 80}")
        for row in cur.fetchall():
            sport, count = row
            print(f"  {sport}: {count} teams")
        
        # Show sample teams
        cur.execute("""
            SELECT team_name, team_abbr, sport, wins, losses, conference, division
            FROM teams
            ORDER BY sport, team_name
            LIMIT 10
        """)
        
        print(f"\n{'=' * 80}")
        print("Sample Teams:")
        print(f"{'=' * 80}")
        print(f"{'Team Name':<30} {'Abbr':<6} {'Sport':<6} {'Record':<10} {'Conference':<15} {'Division':<20}")
        print("-" * 80)
        for row in cur.fetchall():
            name, abbr, sport, wins, losses, conf, div = row
            record = f"{wins or 0}-{losses or 0}"
            print(f"{name:<30} {abbr:<6} {sport:<6} {record:<10} {conf or 'N/A':<15} {div or 'N/A':<20}")
        
        cur.close()
        conn.close()
        
        print(f"\n✅ Successfully populated teams table!")
        
    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
