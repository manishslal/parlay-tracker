#!/usr/bin/env python3
"""Create remaining indexes with correct column names"""
import psycopg2

DATABASE_URL = 'postgresql://parlays_user:wgEpC1q34LIekYv6uelYqSThFdoy8xJT@dpg-d43b4iripnbc73bmuv5g-a.virginia-postgres.render.com/parlays'

# Additional useful indexes based on actual schema
INDEXES = [
    # Players - index current_team since that's how we join to teams
    "CREATE INDEX IF NOT EXISTS idx_players_current_team ON players(current_team)",
    "CREATE INDEX IF NOT EXISTS idx_players_espn_id ON players(espn_player_id)",
    
    # Teams - additional useful indexes
    "CREATE INDEX IF NOT EXISTS idx_teams_espn_id ON teams(espn_team_id)",
    "CREATE INDEX IF NOT EXISTS idx_teams_abbr ON teams(team_abbr)",
    
    # Bets - user lookup is critical
    "CREATE INDEX IF NOT EXISTS idx_bets_user_id ON bets(user_id)",
    
    # Bet_legs - opponent and team matching
    "CREATE INDEX IF NOT EXISTS idx_bet_legs_home_team ON bet_legs(home_team)",
    "CREATE INDEX IF NOT EXISTS idx_bet_legs_away_team ON bet_legs(away_team)",
]

def main():
    print(f"Connecting to production database...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    print(f"\nCreating {len(INDEXES)} additional indexes...")
    
    for i, index_sql in enumerate(INDEXES, 1):
        try:
            print(f"  [{i}/{len(INDEXES)}] {index_sql[:70]}...")
            cur.execute(index_sql)
            conn.commit()
            print(f"  ✅ Created")
        except Exception as e:
            print(f"  ⚠️  Error: {e}")
            conn.rollback()
    
    # Show summary of all indexes
    print(f"\n=== ALL INDEXES ON KEY TABLES ===")
    for table in ['bets', 'bet_legs', 'players', 'teams']:
        cur.execute(f"""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = '{table}' 
            AND indexname LIKE 'idx_%'
            ORDER BY indexname
        """)
        indexes = [row[0] for row in cur.fetchall()]
        print(f"\n{table.upper()} ({len(indexes)} indexes):")
        for idx in indexes:
            print(f"  - {idx}")
    
    cur.close()
    conn.close()
    print(f"\n✅ Done!")

if __name__ == '__main__':
    main()
