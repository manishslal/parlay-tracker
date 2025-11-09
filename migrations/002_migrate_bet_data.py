#!/usr/bin/env python3
"""
Migration 002: Migrate Existing Bet Data
Purpose: Parse bet_data JSON and populate new structured tables
Safe: Only reads and populates, doesn't delete anything
"""

import os
import sys
import json
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    """Get database connection from environment"""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set!")
        print("\nTo set it, run:")
        print("export DATABASE_URL='postgresql://...'")
        sys.exit(1)
    
    # Fix Render's postgres:// to postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    return psycopg2.connect(database_url, cursor_factory=RealDictCursor)

def normalize_name(name):
    """Normalize player name for matching"""
    return name.lower().strip()

def extract_sport_from_context(leg_data):
    """Try to determine sport from leg data"""
    # Check position for sport clues
    position = leg_data.get('position', '').upper()
    
    # NFL positions
    if position in ['QB', 'RB', 'WR', 'TE', 'K', 'P']:
        return 'NFL'
    
    # NBA positions
    if position in ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F']:
        return 'NBA'
    
    # MLB positions
    if position in ['SP', 'RP', 'CP', 'C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'DH', 'P']:
        return 'MLB'
    
    # Check bet type for sport clues
    bet_type = leg_data.get('stat', '').lower()
    if 'passing' in bet_type or 'rushing' in bet_type or 'receiving' in bet_type:
        return 'NFL'
    if 'points' in bet_type or 'rebounds' in bet_type or 'assists' in bet_type:
        return 'NBA'
    if 'hits' in bet_type or 'runs' in bet_type or 'strikeouts' in bet_type or 'era' in bet_type:
        return 'MLB'
    
    # Default to NFL (most common in existing data)
    return 'NFL'

def get_or_create_player(cursor, player_name, team, position, sport):
    """Get existing player or create new one"""
    normalized = normalize_name(player_name)
    
    # Check if player already exists
    cursor.execute("""
        SELECT id FROM players 
        WHERE normalized_name = %s AND sport = %s
    """, (normalized, sport))
    
    result = cursor.fetchone()
    if result:
        return result['id'] if isinstance(result, dict) else result[0]
    
    # Create new player
    cursor.execute("""
        INSERT INTO players (
            player_name, normalized_name, display_name,
            sport, position, current_team, data_source
        ) VALUES (%s, %s, %s, %s, %s, %s, 'migration')
        RETURNING id
    """, (player_name, normalized, player_name, sport, position, team))
    
    result = cursor.fetchone()
    return result['id'] if isinstance(result, dict) else result[0]

def migrate_bet(cursor, bet_row):
    """Migrate a single bet from JSON to structured format"""
    bet_id = bet_row['id']
    bet_data = json.loads(bet_row['bet_data'])
    
    print(f"  Migrating bet {bet_id}: {bet_data.get('name', 'Unknown')}")
    
    # Extract bet-level data
    wager = float(bet_data.get('wager') or 0)
    
    # Handle odds - may be int or string like '3x'
    odds_value = bet_data.get('odds')
    if odds_value:
        # Try to parse as int, if fails (like '3x'), extract number or default to 0
        try:
            odds = int(odds_value)
        except (ValueError, TypeError):
            # Try to extract digits from string like '3x'
            import re
            match = re.search(r'(\d+)', str(odds_value))
            odds = int(match.group(1)) if match else 0
    else:
        odds = 0
    
    returns = float(bet_data.get('returns') or 0)
    legs = bet_data.get('legs', [])
    
    # Calculate potential winnings
    potential_winnings = returns if returns > 0 else 0
    
    # Determine if won
    bet_status = bet_row['status']
    actual_winnings = returns if bet_status == 'won' else 0 if bet_status in ['lost', 'pending'] else None
    
    # Count leg statuses
    legs_won = sum(1 for leg in legs if leg.get('status') == 'won')
    legs_lost = sum(1 for leg in legs if leg.get('status') == 'lost')
    legs_live = sum(1 for leg in legs if leg.get('status') == 'live')
    legs_pending = sum(1 for leg in legs if leg.get('status') in ['pending', None])
    total_legs = len(legs)
    
    # Update bet table with new columns
    cursor.execute("""
        UPDATE bets SET
            wager = %s,
            final_odds = %s,
            potential_winnings = %s,
            actual_winnings = %s,
            total_legs = %s,
            legs_won = %s,
            legs_lost = %s,
            legs_pending = %s,
            legs_live = %s
        WHERE id = %s
    """, (wager, odds, potential_winnings, actual_winnings,
          total_legs, legs_won, legs_lost, legs_pending, legs_live, bet_id))
    
    # Migrate each leg
    for idx, leg in enumerate(legs, 1):
        migrate_leg(cursor, bet_id, leg, idx, bet_data.get('type', 'Parlay'))
    
    return len(legs)

def migrate_leg(cursor, bet_id, leg_data, leg_order, bet_type):
    """Create bet_leg record from leg data"""
    
    # Extract player info
    player_name = leg_data.get('player', 'Unknown')
    player_team = leg_data.get('team', '')
    player_position = leg_data.get('position', '')
    
    # Extract game info
    opponent = leg_data.get('opponent', '')
    home_team = ''
    away_team = ''
    
    # Try to determine home/away from @ symbol
    if '@' in opponent:
        away_team = player_team
        home_team = opponent.replace('@', '').strip()
    else:
        home_team = player_team
        away_team = opponent.strip()
    
    # Determine sport
    sport = extract_sport_from_context(leg_data)
    parlay_sport = sport  # Same for now, can be different if mixed-sport parlays
    
    # Get or create player
    player_id = get_or_create_player(cursor, player_name, player_team, player_position, sport)
    
    # Extract bet details
    bet_stat_type = leg_data.get('stat', '')
    target_value = float(leg_data.get('target', 0))
    achieved_value = leg_data.get('current')
    achieved_value = float(achieved_value) if achieved_value not in [None, '-'] else None
    
    # Determine line type (over/under)
    bet_line_type = None
    if 'over' in bet_stat_type.lower():
        bet_line_type = 'over'
    elif 'under' in bet_stat_type.lower():
        bet_line_type = 'under'
    
    # Extract stat type
    stat_type = None
    if 'yard' in bet_stat_type.lower():
        stat_type = 'yards'
    elif 'point' in bet_stat_type.lower():
        stat_type = 'points'
    elif 'reception' in bet_stat_type.lower():
        stat_type = 'receptions'
    elif 'td' in bet_stat_type.lower() or 'touchdown' in bet_stat_type.lower():
        stat_type = 'touchdowns'
    
    # Get status
    status = leg_data.get('status', 'pending')
    is_hit = True if status == 'won' else False if status == 'lost' else None
    
    # Game ID from leg data
    game_id = leg_data.get('gameId', '')
    
    # Insert bet_leg
    cursor.execute("""
        INSERT INTO bet_legs (
            bet_id, player_id, player_name, player_team, player_position,
            home_team, away_team, game_id, sport, parlay_sport,
            bet_type, bet_line_type, target_value, achieved_value, stat_type,
            status, is_hit, leg_order
        ) VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s
        )
    """, (
        bet_id, player_id, player_name, player_team, player_position,
        home_team, away_team, game_id, sport, parlay_sport,
        bet_stat_type, bet_line_type, target_value, achieved_value, stat_type,
        status, is_hit, leg_order
    ))

def calculate_tax_data(cursor):
    """Calculate tax_data for all users"""
    print("\n📊 Calculating tax data...")
    
    # Get all users
    cursor.execute("SELECT id FROM users")
    users = cursor.fetchall()
    
    for user in users:
        user_id = user['id'] if isinstance(user, dict) else user[0]
        
        # Get unique years from user's bets
        cursor.execute("""
            SELECT DISTINCT EXTRACT(YEAR FROM bet_date::date) as year
            FROM bets
            WHERE user_id = %s AND bet_date IS NOT NULL
            ORDER BY year
        """, (user_id,))
        
        years = cursor.fetchall()
        
        for year_row in years:
            year = int(year_row['year'])
            
            # Calculate yearly stats
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(wager), 0) as total_wagered,
                    COALESCE(SUM(actual_winnings), 0) as total_winnings,
                    COALESCE(SUM(actual_winnings - wager), 0) as net_profit,
                    COUNT(*) as total_bets,
                    SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END) as winning_bets,
                    SUM(CASE WHEN status = 'lost' THEN 1 ELSE 0 END) as losing_bets
                FROM bets
                WHERE user_id = %s 
                AND EXTRACT(YEAR FROM bet_date::date) = %s
                AND wager IS NOT NULL
            """, (user_id, year))
            
            stats = cursor.fetchone()
            
            if stats and stats['total_bets'] > 0:  # If there are bets
                cursor.execute("""
                    INSERT INTO tax_data (
                        user_id, tax_year, total_wagered, total_winnings, net_profit,
                        total_bets, winning_bets, losing_bets
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, tax_year) 
                    DO UPDATE SET
                        total_wagered = EXCLUDED.total_wagered,
                        total_winnings = EXCLUDED.total_winnings,
                        net_profit = EXCLUDED.net_profit,
                        total_bets = EXCLUDED.total_bets,
                        winning_bets = EXCLUDED.winning_bets,
                        losing_bets = EXCLUDED.losing_bets,
                        last_calculated = NOW()
                """, (user_id, year, stats['total_wagered'], stats['total_winnings'], stats['net_profit'], 
                      stats['total_bets'], stats['winning_bets'], stats['losing_bets']))
                
                print(f"  User {user_id} - {year}: {stats['total_bets']} bets, ${stats['net_profit']:.2f} profit")

def main():
    print("🚀 Starting Data Migration...")
    print("=" * 60)
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get all bets
        cursor.execute("""
            SELECT id, user_id, bet_data, status, bet_date
            FROM bets
            ORDER BY id
        """)
        bets = cursor.fetchall()
        
        print(f"\n📦 Found {len(bets)} bets to migrate\n")
        
        total_legs = 0
        for bet in bets:
            legs_count = migrate_bet(cursor, bet)
            total_legs += legs_count
        
        print(f"\n✅ Migrated {len(bets)} bets with {total_legs} total legs")
        
        # Calculate tax data
        calculate_tax_data(cursor)
        
        # Mark migration as complete
        cursor.execute("""
            INSERT INTO schema_migrations (migration_name)
            VALUES ('002_migrate_bet_data')
            ON CONFLICT (migration_name) DO NOTHING
        """)
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERROR during migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()
