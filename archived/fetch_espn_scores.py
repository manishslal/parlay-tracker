"""
Fetch historical game scores from ESPN API and populate bet_legs table.

ESPN API structure for NFL games:
https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=YYYYMMDD
"""

import os
import sys
import time
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta

def fetch_espn_game_score(date_str, away_team, home_team):
    """
    Fetch game score from ESPN API for a specific date and matchup.
    
    Args:
        date_str: Date in YYYY-MM-DD format
        away_team: Full away team name (e.g., "Las Vegas Raiders")
        home_team: Full home team name (e.g., "Denver Broncos")
    
    Returns:
        dict with away_score, home_score, and status or None if not found
    """
    try:
        # Convert date to YYYYMMDD format for ESPN API
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        espn_date = date_obj.strftime('%Y%m%d')
        
        url = f'https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={espn_date}'
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"  ⚠️  ESPN API returned {response.status_code} for {date_str}")
            return None
        
        data = response.json()
        events = data.get('events', [])
        
        # Find matching game
        for event in events:
            competitions = event.get('competitions', [])
            if not competitions:
                continue
            
            competition = competitions[0]
            competitors = competition.get('competitors', [])
            
            if len(competitors) < 2:
                continue
            
            # ESPN has competitors as list, one is home, one is away
            home_competitor = next((c for c in competitors if c.get('homeAway') == 'home'), None)
            away_competitor = next((c for c in competitors if c.get('homeAway') == 'away'), None)
            
            if not home_competitor or not away_competitor:
                continue
            
            espn_home = home_competitor.get('team', {}).get('displayName', '')
            espn_away = away_competitor.get('team', {}).get('displayName', '')
            
            # Match teams (case-insensitive, partial match)
            home_match = home_team.lower() in espn_home.lower() or espn_home.lower() in home_team.lower()
            away_match = away_team.lower() in espn_away.lower() or espn_away.lower() in away_team.lower()
            
            if home_match and away_match:
                # Found the game!
                home_score = int(home_competitor.get('score', 0))
                away_score = int(away_competitor.get('score', 0))
                status = competition.get('status', {}).get('type', {}).get('name', 'unknown')
                
                return {
                    'away_score': away_score,
                    'home_score': home_score,
                    'status': status,
                    'espn_home': espn_home,
                    'espn_away': espn_away
                }
        
        print(f"  ⚠️  No match found for {away_team} @ {home_team} on {date_str}")
        return None
        
    except Exception as e:
        print(f"  ❌ Error fetching ESPN data: {e}")
        return None

def populate_scores_from_espn():
    """Fetch scores from ESPN API and populate bet_legs table."""
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        return
    
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    if 'sslmode' not in database_url:
        database_url += '?sslmode=require'
    
    print("Connecting to database...")
    conn = psycopg2.connect(database_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get all legs that need scores (completed bets without scores)
        cur.execute("""
            SELECT bl.id, bl.bet_id, bl.player_name, bl.home_team, bl.away_team, 
                   bl.game_date, bl.home_score, bl.away_score, b.status
            FROM bet_legs bl
            JOIN bets b ON bl.bet_id = b.id
            WHERE b.status IN ('completed', 'lost', 'won')
            AND bl.game_date IS NOT NULL
            AND bl.home_team IS NOT NULL
            AND bl.away_team IS NOT NULL
            AND (bl.home_score IS NULL OR bl.away_score IS NULL)
            ORDER BY bl.game_date DESC, bl.bet_id
        """)
        
        legs_to_update = cur.fetchall()
        print(f"Found {len(legs_to_update)} legs needing scores\n")
        
        if not legs_to_update:
            print("✅ All legs already have scores!")
            return
        
        # Group by game (same date + same teams = same game)
        games_cache = {}
        updated_legs = 0
        api_calls = 0
        
        for leg in legs_to_update:
            leg_id = leg['id']
            player_name = leg['player_name']
            home_team = leg['home_team']
            away_team = leg['away_team']
            game_date = str(leg['game_date'])
            
            # Create cache key
            game_key = f"{game_date}|{away_team}|{home_team}"
            
            # Check cache first
            if game_key not in games_cache:
                print(f"Fetching: {away_team} @ {home_team} on {game_date}")
                
                # Fetch from ESPN
                score_data = fetch_espn_game_score(game_date, away_team, home_team)
                games_cache[game_key] = score_data
                
                api_calls += 1
                
                # Rate limiting
                if api_calls % 5 == 0:
                    print(f"  (Rate limiting: waiting 2 seconds...)")
                    time.sleep(2)
                else:
                    time.sleep(0.3)
            
            score_data = games_cache[game_key]
            
            if score_data:
                # Update the leg with scores
                cur.execute("""
                    UPDATE bet_legs
                    SET home_score = %s, away_score = %s, updated_at = NOW()
                    WHERE id = %s
                """, (score_data['home_score'], score_data['away_score'], leg_id))
                
                updated_legs += 1
                print(f"  ✅ {player_name}: {score_data['espn_away']} {score_data['away_score']} - {score_data['home_score']} {score_data['espn_home']}")
        
        # Commit all changes
        conn.commit()
        
        print(f"\n{'='*60}")
        print(f"✅ Successfully updated {updated_legs} bet legs")
        print(f"   Made {api_calls} ESPN API calls")
        print(f"   Unique games: {len(games_cache)}")
        print(f"{'='*60}")
        
        # Show sample results
        cur.execute("""
            SELECT bl.player_name, bl.bet_type, bl.home_score, bl.away_score, 
                   bl.home_team, bl.away_team, bl.game_date
            FROM bet_legs bl
            JOIN bets b ON bl.bet_id = b.id
            WHERE bl.home_score IS NOT NULL
            AND b.status IN ('completed', 'lost', 'won')
            ORDER BY bl.game_date DESC
            LIMIT 5
        """)
        
        samples = cur.fetchall()
        if samples:
            print("\nSample updated legs:")
            for s in samples:
                print(f"  {s['game_date']}: {s['player_name']} - "
                      f"{s['away_team']} {s['away_score']} - {s['home_score']} {s['home_team']}")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    populate_scores_from_espn()
