"""
Step 1: Populate game_date, home_team, away_team in bet_legs from JSON.
Step 2: Fetch scores from ESPN API and update bet_legs.
"""

import os
import sys
import time
import json
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

def populate_game_info_from_json():
    """First, populate missing game info from JSON."""
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        return False
    
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    if 'sslmode' not in database_url:
        database_url += '?sslmode=require'
    
    print("="*60)
    print("STEP 1: Populating game info from JSON")
    print("="*60)
    
    conn = psycopg2.connect(database_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get all bets with JSON data
        cur.execute("""
            SELECT id, bet_data
            FROM bets
            WHERE bet_data IS NOT NULL
            ORDER BY id
        """)
        
        bets = cur.fetchall()
        updated_legs = 0
        
        for bet in bets:
            bet_id = bet['id']
            bet_data = bet['bet_data']
            
            if isinstance(bet_data, str):
                try:
                    bet_data = json.loads(bet_data)
                except:
                    continue
            
            legs = bet_data.get('legs', [])
            
            for i, json_leg in enumerate(legs):
                home = json_leg.get('home')
                away = json_leg.get('away')
                game_date = json_leg.get('game_date')
                
                if not home or not away:
                    continue
                
                # Update the corresponding bet_leg
                # First, get the leg ID
                cur.execute("""
                    SELECT id
                    FROM bet_legs
                    WHERE bet_id = %s
                    AND (home_team IS NULL OR home_team = '' OR away_team IS NULL OR away_team = '')
                    ORDER BY leg_order
                    LIMIT 1 OFFSET %s
                """, (bet_id, i))
                
                leg_row = cur.fetchone()
                if not leg_row:
                    continue
                
                # Now update it
                cur.execute("""
                    UPDATE bet_legs
                    SET home_team = %s, 
                        away_team = %s, 
                        game_date = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    RETURNING player_name
                """, (home, away, game_date, leg_row['id']))
                
                result = cur.fetchone()
                if result:
                    updated_legs += 1
        
        conn.commit()
        print(f"✅ Updated {updated_legs} legs with game info from JSON\n")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def fetch_espn_game_score(date_str, away_team, home_team):
    """Fetch game score from ESPN API."""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        espn_date = date_obj.strftime('%Y%m%d')
        
        url = f'https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={espn_date}'
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        events = data.get('events', [])
        
        for event in events:
            competitions = event.get('competitions', [])
            if not competitions:
                continue
            
            competition = competitions[0]
            competitors = competition.get('competitors', [])
            
            if len(competitors) < 2:
                continue
            
            home_competitor = next((c for c in competitors if c.get('homeAway') == 'home'), None)
            away_competitor = next((c for c in competitors if c.get('homeAway') == 'away'), None)
            
            if not home_competitor or not away_competitor:
                continue
            
            espn_home = home_competitor.get('team', {}).get('displayName', '')
            espn_away = away_competitor.get('team', {}).get('displayName', '')
            
            # Match teams
            home_match = home_team.lower() in espn_home.lower() or espn_home.lower() in home_team.lower()
            away_match = away_team.lower() in espn_away.lower() or espn_away.lower() in away_team.lower()
            
            if home_match and away_match:
                home_score = int(home_competitor.get('score', 0))
                away_score = int(away_competitor.get('score', 0))
                
                return {
                    'away_score': away_score,
                    'home_score': home_score,
                    'espn_home': espn_home,
                    'espn_away': espn_away
                }
        
        return None
        
    except Exception as e:
        return None

def fetch_scores_from_espn():
    """Fetch scores from ESPN and populate bet_legs."""
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        return
    
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    if 'sslmode' not in database_url:
        database_url += '?sslmode=require'
    
    print("="*60)
    print("STEP 2: Fetching scores from ESPN API")
    print("="*60)
    
    conn = psycopg2.connect(database_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get legs needing scores
        cur.execute("""
            SELECT bl.id, bl.player_name, bl.home_team, bl.away_team, 
                   bl.game_date
            FROM bet_legs bl
            JOIN bets b ON bl.bet_id = b.id
            WHERE b.status IN ('completed', 'lost', 'won')
            AND bl.game_date IS NOT NULL
            AND bl.home_team IS NOT NULL AND bl.home_team != ''
            AND bl.away_team IS NOT NULL AND bl.away_team != ''
            AND (bl.home_score IS NULL OR bl.away_score IS NULL)
            ORDER BY bl.game_date DESC
        """)
        
        legs_to_update = cur.fetchall()
        print(f"Found {len(legs_to_update)} legs needing scores\n")
        
        games_cache = {}
        updated_legs = 0
        api_calls = 0
        
        for leg in legs_to_update:
            leg_id = leg['id']
            player_name = leg['player_name']
            home_team = leg['home_team']
            away_team = leg['away_team']
            game_date = str(leg['game_date'])
            
            game_key = f"{game_date}|{away_team}|{home_team}"
            
            if game_key not in games_cache:
                print(f"Fetching: {away_team} @ {home_team} on {game_date}")
                score_data = fetch_espn_game_score(game_date, away_team, home_team)
                games_cache[game_key] = score_data
                
                api_calls += 1
                if api_calls % 5 == 0:
                    time.sleep(2)
                else:
                    time.sleep(0.3)
            
            score_data = games_cache[game_key]
            
            if score_data:
                cur.execute("""
                    UPDATE bet_legs
                    SET home_score = %s, away_score = %s, updated_at = NOW()
                    WHERE id = %s
                """, (score_data['home_score'], score_data['away_score'], leg_id))
                
                updated_legs += 1
                print(f"  ✅ {player_name}: {score_data['away_score']} - {score_data['home_score']}")
        
        conn.commit()
        
        print(f"\n{'='*60}")
        print(f"✅ Successfully updated {updated_legs} legs with scores")
        print(f"   Made {api_calls} ESPN API calls")
        print(f"{'='*60}")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    # Step 1: Populate game info from JSON
    if populate_game_info_from_json():
        # Step 2: Fetch scores from ESPN
        fetch_scores_from_espn()
