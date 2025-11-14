#!/usr/bin/env python3
"""
Populate missing game dates for bet_legs by looking up games from ESPN API.
This script finds bet_legs with missing game_date and attempts to find the game
based on player_team and the date the bet was placed.
"""

import os
import sys
import time
import psycopg2
import requests
from datetime import datetime, timedelta

def get_team_espn_id(team_name, sport):
    """Get ESPN team ID from our teams table."""
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'), sslmode='require')
        cur = conn.cursor()
        
        # Try exact team name match first
        cur.execute("""
            SELECT espn_team_id FROM teams 
            WHERE team_name = %s AND sport = %s
        """, (team_name, sport))
        
        result = cur.fetchone()
        
        # If no exact match, try abbreviation
        if not result:
            cur.execute("""
                SELECT espn_team_id FROM teams 
                WHERE team_abbr = %s AND sport = %s
            """, (team_name, sport))
            result = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return result[0] if result else None
    except Exception as e:
        print(f"Error getting team ID for {team_name}: {e}")
        return None

def fetch_team_schedule(sport, team_id, year=2025):
    """Fetch team schedule from ESPN API."""
    try:
        if sport == 'NFL':
            url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}/schedule?season={year}"
        elif sport == 'NBA':
            url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/schedule?season={year}"
        else:
            return None
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        time.sleep(0.3)  # Rate limiting
        
        return response.json()
    except Exception as e:
        print(f"Error fetching schedule for team {team_id}: {e}")
        return None

def find_game_date(sport, team_name, bet_created_at):
    """Find the next game date after the bet was placed."""
    team_id = get_team_espn_id(team_name, sport)
    if not team_id:
        return None, None, None, None
    
    schedule_data = fetch_team_schedule(sport, team_id)
    if not schedule_data:
        return None, None, None, None
    
    events = schedule_data.get('events', [])
    bet_date = bet_created_at.date() if isinstance(bet_created_at, datetime) else bet_created_at
    
    # Find games after the bet was placed
    for event in events:
        event_date_str = event.get('date', '')
        if not event_date_str:
            continue
        
        # Parse event date and convert to Eastern time
        event_dt = datetime.fromisoformat(event_date_str.replace('Z', '+00:00'))
        event_date_eastern = (event_dt - timedelta(hours=5)).date()
        
        # Only consider games scheduled after the bet was placed
        if event_date_eastern >= bet_date:
            # Get home and away teams
            competitions = event.get('competitions', [])
            if competitions:
                comp = competitions[0]
                competitors = comp.get('competitors', [])
                
                home_team = None
                away_team = None
                game_id = event.get('id')
                
                for competitor in competitors:
                    team = competitor.get('team', {})
                    team_abbr_espn = team.get('abbreviation', '')
                    is_home = competitor.get('homeAway') == 'home'
                    
                    if is_home:
                        home_team = team_abbr_espn
                    else:
                        away_team = team_abbr_espn
                
                # Return the first game found after bet was placed
                return event_date_eastern, home_team, away_team, game_id
    
    return None, None, None, None

def update_missing_game_dates():
    """Update all bet_legs that are missing game_date."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        return False
    
    try:
        conn = psycopg2.connect(database_url, sslmode='require')
        cur = conn.cursor()
        
        print("🔄 Finding bet_legs with missing game_date...")
        print("=" * 80)
        
        # Get all bet_legs without game_date
        cur.execute("""
            SELECT id, player_name, player_team, sport, created_at
            FROM bet_legs
            WHERE game_date IS NULL AND player_team IS NOT NULL
            ORDER BY created_at DESC
        """)
        
        missing_legs = cur.fetchall()
        total = len(missing_legs)
        
        print(f"Found {total} bet_legs with missing game_date\n")
        
        if total == 0:
            print("✅ All bet_legs already have game dates!")
            return True
        
        updated = 0
        failed = 0
        
        # Group by team to minimize API calls
        team_cache = {}
        
        for leg_id, player_name, team_name, sport, created_at in missing_legs:
            # Skip if no team name
            if not team_name or team_name.strip() == '':
                print(f"  ⚠️  {leg_id:3} | {player_name:25} | (No team) | Skipping")
                failed += 1
                continue
            
            cache_key = f"{sport}:{team_name}:{created_at.date()}"
            
            if cache_key not in team_cache:
                game_date, home_team, away_team, game_id = find_game_date(sport, team_name, created_at)
                team_cache[cache_key] = (game_date, home_team, away_team, game_id)
            else:
                game_date, home_team, away_team, game_id = team_cache[cache_key]
            
            if game_date:
                try:
                    cur.execute("""
                        UPDATE bet_legs
                        SET game_date = %s,
                            home_team = COALESCE(home_team, %s),
                            away_team = COALESCE(away_team, %s),
                            game_id = COALESCE(game_id, %s),
                            updated_at = NOW()
                        WHERE id = %s
                    """, (game_date, home_team, away_team, game_id, leg_id))
                    conn.commit()
                    updated += 1
                    print(f"  ✅ {leg_id:3} | {player_name:25} | {team_name:30} | {sport} | {game_date}")
                except Exception as e:
                    print(f"  ❌ {leg_id:3} | {player_name:25} | {team_name:30} | Error: {e}")
                    failed += 1
                    conn.rollback()
            else:
                print(f"  ⚠️  {leg_id:3} | {player_name:25} | {team_name:30} | No game found")
                failed += 1
        
        cur.close()
        conn.close()
        
        print()
        print("=" * 80)
        print("UPDATE SUMMARY")
        print("=" * 80)
        print(f"Total bet_legs checked: {total}")
        print(f"✅ Updated: {updated}")
        print(f"❌ Failed/Not Found: {failed}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("📅 Populating Missing Game Dates")
    print("=" * 80)
    print()
    
    success = update_missing_game_dates()
    sys.exit(0 if success else 1)
