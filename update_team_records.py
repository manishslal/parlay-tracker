#!/usr/bin/env python3
"""
Automated script to update dynamic team data (records, game dates, standings).
This script updates only changing data and skips static fields like league/conference/division.
Can be run daily via cron job or on application startup.
"""

import psycopg2
import os
import sys
import requests
import time
from datetime import datetime, timedelta

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
        return None

def fetch_team_last_game(sport, team_id):
    """Fetch the most recent completed game date for a team."""
    try:
        if sport == 'NFL':
            url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}/schedule"
        elif sport == 'NBA':
            url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/schedule"
        else:
            return None
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        time.sleep(0.3)  # Rate limiting
        
        data = response.json()
        events = data.get('events', [])
        
        # Find most recent completed game (events are chronologically ordered, so we need the LAST completed game)
        last_completed_date = None
        for event in events:
            competitions = event.get('competitions', [])
            if competitions:
                comp = competitions[0]
                status = comp.get('status', {})
                status_type = status.get('type', {})
                if status_type.get('completed'):
                    event_date = event.get('date')
                    if event_date:
                        # Parse UTC datetime and convert to US Eastern time for proper date
                        from datetime import timedelta, timezone
                        utc_dt = datetime.fromisoformat(event_date.replace('Z', '+00:00'))
                        # Convert to EST (UTC-5) or EDT (UTC-4) - using UTC-5 for simplicity
                        eastern_dt = utc_dt - timedelta(hours=5)
                        last_completed_date = eastern_dt.date()
        
        return last_completed_date
    except Exception as e:
        return None

def extract_dynamic_team_data(data):
    """Extract only dynamic/changing team data (records, dates, standings)."""
    team = data.get('team', {})
    
    info = {}
    
    # Extract current season record
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
                    elif stat_name == 'streak':
                        # Streak comes as a number (positive = wins, negative = losses)
                        streak_val = stat_value
                        if streak_val > 0:
                            info['streak'] = f'W{int(streak_val)}'
                        elif streak_val < 0:
                            info['streak'] = f'L{int(abs(streak_val))}'
                        else:
                            info['streak'] = None
                    elif stat_name == 'playoffSeed':
                        info['playoff_seed'] = int(stat_value) if stat_value else None
                    elif stat_name == 'gamesBehind':
                        info['games_behind'] = float(stat_value) if stat_value else None
    
    # Extract standings/ranks from summary
    if 'standingSummary' in team:
        summary = team['standingSummary']
        
        # Extract rank (e.g., "2nd in NFC East" -> division_rank = 2)
        # Format is typically "Xth in [Conference] [Division/Group]" or "Xth in [Division] Division"
        parts = summary.split()
        if parts and parts[0].replace('st', '').replace('nd', '').replace('rd', '').replace('th', '').isdigit():
            rank = int(parts[0].replace('st', '').replace('nd', '').replace('rd', '').replace('th', ''))
            
            # For NFL: "2nd in NFC East" or "3rd in AFC West" = division rank
            # For NBA: "1st in Pacific Division" or "2nd in Eastern Conference" 
            if 'division' in summary.lower():
                info['division_rank'] = rank
            elif 'conference' in summary.lower() and 'division' not in summary.lower():
                # Only conference, not division
                info['conference_rank'] = rank
            elif any(div in summary for div in ['East', 'West', 'North', 'South', 'Atlantic', 'Central', 'Southeast', 'Northwest', 'Pacific', 'Southwest']):
                # It mentions a division name (AFC East, NFC West, Atlantic, etc.)
                info['division_rank'] = rank
    
    # Extract next event/game date
    next_event = team.get('nextEvent', [])
    if next_event and len(next_event) > 0:
        event_date = next_event[0].get('date')
        if event_date:
            try:
                info['next_game_date'] = datetime.fromisoformat(event_date.replace('Z', '+00:00')).date()
            except:
                pass
    
    # Set last update timestamp
    info['last_stats_update'] = datetime.utcnow()
    
    return info

def should_update_team(last_update):
    """Determine if team data should be updated based on last update time."""
    if not last_update:
        return True
    
    # Update if last update was more than 6 hours ago
    time_since_update = datetime.utcnow() - last_update
    return time_since_update > timedelta(hours=6)

def update_team_records():
    """Update only dynamic team data (records, standings, game dates)."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        return False
    
    try:
        conn = psycopg2.connect(database_url, sslmode='require')
        cur = conn.cursor()
        
        print(f"🔄 Starting team data update at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Get teams that need updating
        cur.execute("""
            SELECT id, team_name, team_abbr, espn_team_id, sport, last_stats_update
            FROM teams
            WHERE is_active = TRUE
            ORDER BY sport, team_name
        """)
        
        teams = cur.fetchall()
        total_teams = len(teams)
        updated_count = 0
        skipped_count = 0
        failed_count = 0
        
        print(f"Found {total_teams} teams to check")
        print()
        
        for team_id, team_name, team_abbr, espn_team_id, sport, last_update in teams:
            # Check if update is needed
            if not should_update_team(last_update):
                skipped_count += 1
                continue
            
            try:
                # Fetch latest data
                data = fetch_team_details(sport, espn_team_id)
                if not data:
                    failed_count += 1
                    continue
                
                # Extract dynamic data
                info = extract_dynamic_team_data(data)
                
                if not info:
                    failed_count += 1
                    continue
                
                # Fetch last game date (from schedule)
                last_game = fetch_team_last_game(sport, espn_team_id)
                if last_game:
                    info['last_game_date'] = last_game
                
                # Update only dynamic fields
                cur.execute("""
                    UPDATE teams SET
                        games_played = COALESCE(%s, games_played),
                        wins = COALESCE(%s, wins),
                        losses = COALESCE(%s, losses),
                        ties = COALESCE(%s, ties),
                        win_percentage = COALESCE(%s, win_percentage),
                        division_rank = COALESCE(%s, division_rank),
                        conference_rank = COALESCE(%s, conference_rank),
                        league_rank = COALESCE(%s, league_rank),
                        playoff_seed = COALESCE(%s, playoff_seed),
                        games_behind = COALESCE(%s, games_behind),
                        streak = COALESCE(%s, streak),
                        last_game_date = COALESCE(%s, last_game_date),
                        next_game_date = COALESCE(%s, next_game_date),
                        last_stats_update = %s,
                        updated_at = %s
                    WHERE id = %s
                """, (
                    info.get('games_played'),
                    info.get('wins'),
                    info.get('losses'),
                    info.get('ties'),
                    info.get('win_percentage'),
                    info.get('division_rank'),
                    info.get('conference_rank'),
                    info.get('league_rank'),
                    info.get('playoff_seed'),
                    info.get('games_behind'),
                    info.get('streak'),
                    info.get('last_game_date'),
                    info.get('next_game_date'),
                    info.get('last_stats_update'),
                    datetime.utcnow(),
                    team_id
                ))
                
                conn.commit()
                
                # Show brief update
                record = f"{info.get('wins', 0)}-{info.get('losses', 0)}"
                if info.get('ties', 0) > 0:
                    record += f"-{info.get('ties', 0)}"
                
                print(f"  ✅ {team_name:<30} ({team_abbr:3s}) {record:8s}")
                updated_count += 1
                
            except Exception as e:
                print(f"  ❌ {team_name:<30} Failed: {str(e)[:40]}")
                conn.rollback()
                failed_count += 1
                continue
        
        # Summary
        print()
        print("=" * 80)
        print("UPDATE SUMMARY")
        print("=" * 80)
        print(f"Total teams: {total_teams}")
        print(f"✅ Updated: {updated_count}")
        print(f"⏭️  Skipped (recently updated): {skipped_count}")
        print(f"❌ Failed: {failed_count}")
        
        # Show sample of updated data
        if updated_count > 0:
            cur.execute("""
                SELECT 
                    team_name,
                    team_abbr,
                    sport,
                    wins,
                    losses,
                    ties,
                    next_game_date,
                    last_stats_update
                FROM teams
                WHERE last_stats_update > NOW() - INTERVAL '10 minutes'
                ORDER BY sport, wins DESC
                LIMIT 10
            """)
            
            print()
            print("Recent updates:")
            print("-" * 80)
            for row in cur.fetchall():
                name, abbr, sport, wins, losses, ties, next_game, last_update = row
                record = f"{wins or 0}-{losses or 0}"
                if ties and ties > 0:
                    record += f"-{ties}"
                next_game_str = next_game.strftime('%Y-%m-%d') if next_game else 'TBD'
                print(f"  {name:<30} ({sport}) {record:8s} | Next: {next_game_str}")
        
        cur.close()
        conn.close()
        
        print()
        print(f"✅ Update completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = update_team_records()
    sys.exit(0 if success else 1)
