#!/usr/bin/env python3
"""
Script to update teams table with complete data including conference, division, and records.
Uses detailed team endpoints to get full information.
"""

import psycopg2
import os
import sys
import requests
import time
from datetime import datetime

# NFL Conference/Division mapping
NFL_DIVISIONS = {
    '1': {'conference': 'AFC', 'division': 'AFC East'},
    '2': {'conference': 'AFC', 'division': 'AFC North'},
    '3': {'conference': 'AFC', 'division': 'AFC South'},
    '4': {'conference': 'AFC', 'division': 'AFC West'},
    '5': {'conference': 'NFC', 'division': 'NFC East'},
    '6': {'conference': 'NFC', 'division': 'NFC North'},
    '7': {'conference': 'NFC', 'division': 'NFC South'},
    '8': {'conference': 'NFC', 'division': 'NFC West'},
}

# NBA Conference/Division mapping
NBA_DIVISIONS = {
    '1': {'conference': 'Eastern', 'division': 'Atlantic'},
    '2': {'conference': 'Eastern', 'division': 'Central'},
    '3': {'conference': 'Eastern', 'division': 'Southeast'},
    '4': {'conference': 'Western', 'division': 'Northwest'},
    '5': {'conference': 'Western', 'division': 'Pacific'},
    '6': {'conference': 'Western', 'division': 'Southwest'},
}

def fetch_team_details(sport, team_id):
    """Fetch detailed team information from ESPN API."""
    try:
        if sport == 'NFL':
            url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}"
        elif sport == 'NBA':
            url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}"
        else:
            return None
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        time.sleep(0.3)  # Rate limiting
        return response.json()
    except Exception as e:
        print(f"  ⚠️  Failed to fetch team details: {e}")
        return None

def extract_full_team_info(data, sport):
    """Extract complete team information including conference, division, and records."""
    team = data.get('team', {})
    
    info = {}
    
    # Set league name
    if sport == 'NFL':
        info['league'] = 'National Football League'
    elif sport == 'NBA':
        info['league'] = 'National Basketball Association'
    
    # Extract conference and division from standingSummary (more reliable)
    if 'standingSummary' in team:
        summary = team['standingSummary']
        # Format is like "2nd in NFC East" or "3rd in Eastern Conference"
        
        if ' in ' in summary:
            # Split on " in " to get the conference/division part
            parts = summary.split(' in ', 1)
            if len(parts) == 2:
                conf_div = parts[1].strip()
                
                if sport == 'NFL':
                    # NFL format: "NFC East", "AFC West", etc.
                    if 'NFC' in conf_div:
                        info['conference'] = 'NFC'
                        info['division'] = conf_div  # Full "NFC East"
                    elif 'AFC' in conf_div:
                        info['conference'] = 'AFC'
                        info['division'] = conf_div  # Full "AFC West"
                
                elif sport == 'NBA':
                    # NBA format: "Eastern Conference" or division names like "Atlantic Division"
                    if 'Eastern' in conf_div or 'Western' in conf_div:
                        info['conference'] = 'Eastern' if 'Eastern' in conf_div else 'Western'
                        info['division'] = conf_div
                    else:
                        # It's a division name like "Atlantic Division", "Pacific Division", etc.
                        info['division'] = conf_div
                        # Determine conference from division name (check if division name contains these)
                        eastern_divisions = ['Atlantic', 'Central', 'Southeast']
                        western_divisions = ['Northwest', 'Pacific', 'Southwest']
                        
                        # Check if any eastern division name is in the conf_div string
                        for div in eastern_divisions:
                            if div in conf_div:
                                info['conference'] = 'Eastern'
                                break
                        else:
                            # Check western divisions
                            for div in western_divisions:
                                if div in conf_div:
                                    info['conference'] = 'Western'
                                    break
    
    # Extract record
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
                        info['games_played'] = int(stat_value)
                    elif stat_name == 'wins':
                        info['wins'] = int(stat_value)
                    elif stat_name == 'losses':
                        info['losses'] = int(stat_value)
                    elif stat_name == 'ties':
                        info['ties'] = int(stat_value)
                    elif stat_name == 'winPercent':
                        info['win_percentage'] = float(stat_value)
    
    # Extract streak and standing summary
    if 'standingSummary' in team:
        summary = team['standingSummary']
        info['standing_summary'] = summary
        
        # Try to extract rank from summary (e.g., "1st in AFC East")
        parts = summary.split()
        if parts and parts[0].replace('st', '').replace('nd', '').replace('rd', '').replace('th', '').isdigit():
            rank = int(parts[0].replace('st', '').replace('nd', '').replace('rd', '').replace('th', ''))
            if 'division' in summary.lower():
                info['division_rank'] = rank
            elif 'conference' in summary.lower():
                info['conference_rank'] = rank
    
    # Set season year
    info['season_year'] = '2026'
    
    return info

def update_teams_with_full_data():
    """Update all teams with complete information."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    try:
        print("Connecting to database...")
        conn = psycopg2.connect(database_url, sslmode='require')
        cur = conn.cursor()
        
        # Get all teams that need updates
        cur.execute("""
            SELECT id, team_name, team_abbr, espn_team_id, sport
            FROM teams
            ORDER BY sport, team_name
        """)
        
        teams = cur.fetchall()
        print(f"\nFound {len(teams)} teams to update")
        
        updated_count = 0
        failed_count = 0
        
        for team_id, team_name, team_abbr, espn_team_id, sport in teams:
            try:
                print(f"\n  Processing: {team_name} ({sport})...", end=' ')
                
                # Fetch detailed data
                data = fetch_team_details(sport, espn_team_id)
                if not data:
                    print("❌ Failed to fetch")
                    failed_count += 1
                    continue
                
                # Extract info
                info = extract_full_team_info(data, sport)
                
                if not info:
                    print("⚠️  No data extracted")
                    failed_count += 1
                    continue
                
                # Update database
                cur.execute("""
                    UPDATE teams SET
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
                        season_year = %s,
                        last_stats_update = %s,
                        updated_at = %s
                    WHERE id = %s
                """, (
                    info.get('league'),
                    info.get('conference'),
                    info.get('division'),
                    info.get('games_played', 0),
                    info.get('wins', 0),
                    info.get('losses', 0),
                    info.get('ties', 0),
                    info.get('win_percentage'),
                    info.get('division_rank'),
                    info.get('conference_rank'),
                    info.get('season_year', '2026'),
                    datetime.utcnow(),
                    datetime.utcnow(),
                    team_id
                ))
                
                conn.commit()
                
                # Show what was updated
                record = f"{info.get('wins', 0)}-{info.get('losses', 0)}"
                if info.get('ties', 0) > 0:
                    record += f"-{info.get('ties', 0)}"
                
                division = info.get('division', 'N/A')
                print(f"✅ {record:8s} | {division}")
                
                updated_count += 1
                
            except Exception as e:
                print(f"❌ Error: {e}")
                conn.rollback()
                failed_count += 1
                continue
        
        # Show summary
        print("\n" + "=" * 80)
        print("UPDATE SUMMARY")
        print("=" * 80)
        print(f"Successfully updated: {updated_count}")
        print(f"Failed: {failed_count}")
        
        # Show sample of updated data
        cur.execute("""
            SELECT 
                sport,
                COUNT(*) as total,
                COUNT(CASE WHEN conference IS NOT NULL THEN 1 END) as with_conference,
                COUNT(CASE WHEN division IS NOT NULL THEN 1 END) as with_division,
                COUNT(CASE WHEN games_played > 0 THEN 1 END) as with_records
            FROM teams
            GROUP BY sport
            ORDER BY sport
        """)
        
        print("\n" + "=" * 80)
        print("DATA COMPLETENESS")
        print("=" * 80)
        print(f"{'Sport':<6} {'Total':<8} {'Conference':<12} {'Division':<10} {'Records':<10}")
        print("-" * 80)
        for row in cur.fetchall():
            sport, total, with_conf, with_div, with_rec = row
            print(f"{sport:<6} {total:<8} {with_conf:<12} {with_div:<10} {with_rec:<10}")
        
        # Show sample teams
        cur.execute("""
            SELECT 
                team_name,
                team_abbr,
                sport,
                conference,
                division,
                wins,
                losses,
                ties,
                season_year
            FROM teams
            WHERE sport = 'NFL'
            ORDER BY division, wins DESC
            LIMIT 12
        """)
        
        print("\n" + "=" * 80)
        print("SAMPLE NFL TEAMS (Top teams by division)")
        print("=" * 80)
        print(f"{'Team':<30} {'Abbr':<6} {'Record':<10} {'Division':<20}")
        print("-" * 80)
        for row in cur.fetchall():
            name, abbr, sport, conf, div, wins, losses, ties, year = row
            record = f"{wins or 0}-{losses or 0}"
            if ties and ties > 0:
                record += f"-{ties}"
            print(f"{name:<30} {abbr:<6} {record:<10} {div or 'N/A':<20}")
        
        cur.close()
        conn.close()
        
        print("\n✅ Update completed successfully!")
        
    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    update_teams_with_full_data()
