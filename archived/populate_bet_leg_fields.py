#!/usr/bin/env python3
"""
Comprehensive script to populate missing bet_leg fields:
1. player_team from players table
2. player_position from players table
3. game_id from ESPN API
4. achieved_value from ESPN game stats
5. status based on achieved vs target
6. is_hit based on status
"""

import os
import sys
import time
import psycopg2
import requests
from datetime import datetime, timedelta

def get_espn_game_id(sport, home_team, away_team, game_date):
    """Get ESPN game ID from team abbreviations and date."""
    try:
        # First, get team IDs from our database
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'), sslmode='require')
        cur = conn.cursor()
        
        # Try to find either team
        cur.execute("""
            SELECT espn_team_id FROM teams 
            WHERE team_abbr = %s AND sport = %s
        """, (home_team or away_team, sport))
        
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if not result:
            return None
        
        team_id = result[0]
        year = game_date.year if hasattr(game_date, 'year') else 2025
        
        # Fetch schedule
        if sport == 'NFL':
            url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}/schedule?season={year}"
        elif sport == 'NBA':
            url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/schedule?season={year}"
        else:
            return None
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        time.sleep(0.3)
        
        data = response.json()
        events = data.get('events', [])
        
        # Find game on the specified date
        for event in events:
            event_date_str = event.get('date', '')
            if event_date_str:
                event_dt = datetime.fromisoformat(event_date_str.replace('Z', '+00:00'))
                event_date_eastern = (event_dt - timedelta(hours=5)).date()
                
                if event_date_eastern == game_date:
                    return event.get('id')
        
        return None
    except Exception as e:
        print(f"Error getting game ID: {e}")
        return None

def get_player_stats_from_game(sport, game_id, player_name):
    """Get player's actual stats from a specific game."""
    try:
        if sport == 'NFL':
            url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={game_id}"
        elif sport == 'NBA':
            url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={game_id}"
        else:
            return {}
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        time.sleep(0.3)
        
        data = response.json()
        
        # Look through boxscore for player
        boxscore = data.get('boxscore', {})
        players_data = boxscore.get('players', [])
        
        for team_data in players_data:
            statistics = team_data.get('statistics', [])
            for stat_group in statistics:
                athletes = stat_group.get('athletes', [])
                for athlete in athletes:
                    athlete_name = athlete.get('athlete', {}).get('displayName', '')
                    if player_name.lower() in athlete_name.lower() or athlete_name.lower() in player_name.lower():
                        # Found the player, extract stats
                        stats_list = athlete.get('stats', [])
                        labels = stat_group.get('labels', [])
                        
                        stats_dict = {}
                        for i, label in enumerate(labels):
                            if i < len(stats_list):
                                try:
                                    stats_dict[label.lower()] = float(stats_list[i])
                                except:
                                    stats_dict[label.lower()] = stats_list[i]
                        
                        return stats_dict
        
        return {}
    except Exception as e:
        print(f"Error getting player stats: {e}")
        return {}

def calculate_achieved_value(stats, stat_type, sport):
    """Calculate the achieved value based on stat type."""
    if not stats:
        return None
    
    stat_type_lower = stat_type.lower() if stat_type else ''
    
    # Common stat mappings
    if 'pass' in stat_type_lower and 'yard' in stat_type_lower:
        return stats.get('passingyards') or stats.get('pyds') or stats.get('passing yards')
    elif 'rush' in stat_type_lower and 'yard' in stat_type_lower:
        return stats.get('rushingyards') or stats.get('ryds') or stats.get('rushing yards')
    elif 'rec' in stat_type_lower and 'yard' in stat_type_lower:
        return stats.get('receivingyards') or stats.get('recyds') or stats.get('receiving yards')
    elif 'reception' in stat_type_lower or 'rec' == stat_type_lower:
        return stats.get('receptions') or stats.get('rec')
    elif 'point' in stat_type_lower or 'pts' in stat_type_lower:
        return stats.get('points') or stats.get('pts')
    elif 'rebound' in stat_type_lower or 'reb' in stat_type_lower:
        return stats.get('rebounds') or stats.get('reb') or stats.get('totreb')
    elif 'assist' in stat_type_lower or 'ast' in stat_type_lower:
        return stats.get('assists') or stats.get('ast')
    elif 'yard' in stat_type_lower:
        # Generic yards - try multiple sources
        return (stats.get('yards') or stats.get('yds') or 
                stats.get('totyard') or stats.get('totalyards'))
    
    return None

def populate_missing_fields():
    """Main function to populate all missing fields."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        return False
    
    try:
        conn = psycopg2.connect(database_url, sslmode='require')
        cur = conn.cursor()
        
        print("🔄 STEP 1: Populating player_team and player_position from players table")
        print("=" * 80)
        
        # Populate player_team and player_position
        cur.execute("""
            UPDATE bet_legs bl
            SET player_team = p.current_team,
                player_position = p.position
            FROM players p
            WHERE bl.player_id = p.id 
              AND (bl.player_team IS NULL OR bl.player_team = '')
              AND p.current_team IS NOT NULL
        """)
        team_updated = cur.rowcount
        conn.commit()
        print(f"✅ Updated {team_updated} bet_legs with player_team/position from players table\n")
        
        print("🔄 STEP 2: Populating game_id from ESPN API")
        print("=" * 80)
        
        # Get bet_legs without game_id
        cur.execute("""
            SELECT id, sport, home_team, away_team, game_date
            FROM bet_legs
            WHERE (game_id IS NULL OR game_id = '')
              AND home_team IS NOT NULL
              AND away_team IS NOT NULL
              AND game_date IS NOT NULL
            ORDER BY game_date DESC
        """)
        
        legs_need_game_id = cur.fetchall()
        game_id_updated = 0
        
        game_id_cache = {}
        for leg_id, sport, home_team, away_team, game_date in legs_need_game_id:
            cache_key = f"{sport}:{home_team}:{away_team}:{game_date}"
            
            if cache_key not in game_id_cache:
                game_id = get_espn_game_id(sport, home_team, away_team, game_date)
                game_id_cache[cache_key] = game_id
            else:
                game_id = game_id_cache[cache_key]
            
            if game_id:
                cur.execute("""
                    UPDATE bet_legs
                    SET game_id = %s, updated_at = NOW()
                    WHERE id = %s
                """, (game_id, leg_id))
                conn.commit()
                game_id_updated += 1
                print(f"  ✅ Leg {leg_id}: {sport} {home_team} vs {away_team} on {game_date} -> Game ID: {game_id}")
        
        print(f"\n✅ Updated {game_id_updated} bet_legs with game_id\n")
        
        print("🔄 STEP 3: Populating achieved_value for November 2025 games")
        print("=" * 80)
        
        # Get Nov 2025 bet_legs without achieved_value that have game_id
        cur.execute("""
            SELECT id, player_name, sport, game_id, stat_type, target_value
            FROM bet_legs
            WHERE achieved_value IS NULL
              AND game_date >= '2025-11-01' 
              AND game_date < '2025-12-01'
              AND game_id IS NOT NULL
              AND game_id != ''
              AND bet_type NOT IN ('MONEYLINE', 'SPREAD')
            ORDER BY game_date DESC
        """)
        
        legs_need_achieved = cur.fetchall()
        achieved_updated = 0
        
        for leg_id, player_name, sport, game_id, stat_type, target_value in legs_need_achieved:
            stats = get_player_stats_from_game(sport, game_id, player_name)
            if stats:
                achieved = calculate_achieved_value(stats, stat_type, sport)
                if achieved is not None:
                    cur.execute("""
                        UPDATE bet_legs
                        SET achieved_value = %s, updated_at = NOW()
                        WHERE id = %s
                    """, (achieved, leg_id))
                    conn.commit()
                    achieved_updated += 1
                    
                    hit = achieved >= target_value if target_value else False
                    symbol = "✅" if hit else "❌"
                    print(f"  {symbol} Leg {leg_id}: {player_name} {stat_type} -> {achieved} (target: {target_value})")
        
        print(f"\n✅ Updated {achieved_updated} bet_legs with achieved_value\n")
        
        print("🔄 STEP 4: Updating status and is_hit based on achieved vs target")
        print("=" * 80)
        
        # Update status and is_hit for legs with achieved_value
        cur.execute("""
            UPDATE bet_legs
            SET status = CASE 
                WHEN achieved_value >= target_value THEN 'WON'
                WHEN achieved_value < target_value THEN 'LOST'
                ELSE status
            END,
            is_hit = CASE 
                WHEN achieved_value >= target_value THEN TRUE
                WHEN achieved_value < target_value THEN FALSE
                ELSE is_hit
            END,
            updated_at = NOW()
            WHERE achieved_value IS NOT NULL
              AND target_value IS NOT NULL
              AND bet_type NOT IN ('MONEYLINE', 'SPREAD')
              AND (status IS NULL OR status = '' OR is_hit IS NULL)
        """)
        status_updated = cur.rowcount
        conn.commit()
        print(f"✅ Updated {status_updated} bet_legs with status and is_hit\n")
        
        # Final summary
        print("=" * 80)
        print("FINAL SUMMARY")
        print("=" * 80)
        
        cur.execute("SELECT COUNT(*) FROM bet_legs WHERE player_team IS NULL OR player_team = ''")
        still_no_team = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM bet_legs WHERE game_id IS NULL OR game_id = ''")
        still_no_game_id = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM bet_legs WHERE achieved_value IS NULL AND game_date >= '2025-11-01' AND game_date < '2025-12-01'")
        still_no_achieved = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM bet_legs WHERE is_hit IS NULL AND bet_type NOT IN ('MONEYLINE', 'SPREAD')")
        still_no_is_hit = cur.fetchone()[0]
        
        print(f"Player team/position updated: {team_updated}")
        print(f"Game IDs updated: {game_id_updated}")
        print(f"Achieved values updated: {achieved_updated}")
        print(f"Status/is_hit updated: {status_updated}")
        print()
        print(f"Still missing player_team: {still_no_team}")
        print(f"Still missing game_id: {still_no_game_id}")
        print(f"Still missing achieved_value (Nov 2025): {still_no_achieved}")
        print(f"Still missing is_hit: {still_no_is_hit}")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("📊 Populating Missing Bet Leg Fields")
    print("=" * 80)
    print()
    
    success = populate_missing_fields()
    sys.exit(0 if success else 1)
