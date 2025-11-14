#!/usr/bin/env python3
"""
Update game statuses for active bets by fetching live data from ESPN API.
"""

import os
import sys
import time
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

DATABASE_URL = os.environ.get('DATABASE_URL') or 'postgresql://parlays_user:wgEpC1q34LIekYv6uelYqSThFdoy8xJT@dpg-d43b4iripnbc73bmuv5g-a.virginia-postgres.render.com/parlays'

def fetch_game_status(sport, game_id):
    """Fetch live game status from ESPN API."""
    try:
        if sport == 'NFL':
            url = f'https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={game_id}'
        elif sport == 'NBA':
            url = f'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={game_id}'
        else:
            return None
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        header = data.get('header', {})
        competition = header.get('competitions', [{}])[0]
        status = competition.get('status', {})
        
        # Get status details
        status_type = status.get('type', {})
        state = status_type.get('state', 'scheduled')  # pre, in, post
        completed = status_type.get('completed', False)
        detail = status_type.get('detail', '')
        short_detail = status_type.get('shortDetail', '')
        
        # Get scores
        competitors = competition.get('competitors', [])
        home_score = None
        away_score = None
        
        for comp in competitors:
            score = comp.get('score')
            if comp.get('homeAway') == 'home':
                home_score = int(score) if score else 0
            else:
                away_score = int(score) if score else 0
        
        # Map ESPN state to our game_status
        if state == 'pre':
            game_status = 'scheduled'
        elif state == 'in':
            game_status = 'in_progress'
        elif state == 'post':
            game_status = 'completed' if completed else 'final'
        else:
            game_status = 'scheduled'
        
        return {
            'game_status': game_status,
            'home_score': home_score,
            'away_score': away_score,
            'status_detail': short_detail or detail,
            'completed': completed
        }
        
    except Exception as e:
        print(f"  Error fetching game {game_id}: {e}")
        return None

def update_game_statuses():
    """Update game statuses for all active bets."""
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        print("🔄 Updating game statuses from ESPN API")
        print("=" * 80)
        
        # Get all bet_legs with game_ids that are not completed
        cur.execute("""
            SELECT DISTINCT bl.game_id, bl.sport, bl.home_team, bl.away_team
            FROM bet_legs bl
            JOIN bets b ON bl.bet_id = b.id
            WHERE b.is_active = TRUE
            AND bl.game_id IS NOT NULL
            AND bl.game_id != ''
            AND bl.game_status NOT IN ('completed', 'final')
            ORDER BY bl.sport, bl.game_id
        """)
        
        games_to_check = cur.fetchall()
        print(f"Found {len(games_to_check)} games to check\n")
        
        updated_count = 0
        
        for game in games_to_check:
            game_id = game['game_id']
            sport = game['sport']
            home_team = game['home_team']
            away_team = game['away_team']
            
            print(f"Checking: {sport} - {away_team} @ {home_team} (Game {game_id})")
            
            # Fetch live status
            status_data = fetch_game_status(sport, game_id)
            
            if status_data:
                # Update all bet_legs for this game
                cur.execute("""
                    UPDATE bet_legs
                    SET 
                        game_status = %s,
                        home_score = %s,
                        away_score = %s,
                        updated_at = NOW()
                    WHERE game_id = %s
                    RETURNING id
                """, (
                    status_data['game_status'],
                    status_data['home_score'],
                    status_data['away_score'],
                    game_id
                ))
                
                affected = cur.rowcount
                conn.commit()
                
                print(f"  ✅ {status_data['game_status'].upper()}: {away_team} {status_data['away_score']} - {status_data['home_score']} {home_team}")
                print(f"     Updated {affected} bet legs")
                updated_count += affected
            else:
                print(f"  ⚠️  Could not fetch status")
            
            print()
            time.sleep(0.5)  # Rate limiting
        
        print("=" * 80)
        print(f"✅ Updated {updated_count} bet legs")
        print("=" * 80)
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = update_game_statuses()
    sys.exit(0 if success else 1)
