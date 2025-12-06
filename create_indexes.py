#!/usr/bin/env python3
"""Create performance indexes directly on production database"""
import psycopg2
import os

DATABASE_URL = 'postgresql://parlays_user:wgEpC1q34LIekYv6uelYqSThFdoy8xJT@dpg-d43b4iripnbc73bmuv5g-a.virginia-postgres.render.com/parlays'

# All indexes to create
INDEXES = [
    # Bets table
    "CREATE INDEX IF NOT EXISTS idx_bets_status ON bets(status)",
    "CREATE INDEX IF NOT EXISTS idx_bets_created_at ON bets(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_bets_status_created ON bets(status, created_at)",
    
    # Bet_legs table (most queried)
    "CREATE INDEX IF NOT EXISTS idx_bet_legs_bet_id ON bet_legs(bet_id)",
    "CREATE INDEX IF NOT EXISTS idx_bet_legs_game_date ON bet_legs(game_date)",
    "CREATE INDEX IF NOT EXISTS idx_bet_legs_game_id ON bet_legs(game_id)",
    "CREATE INDEX IF NOT EXISTS idx_bet_legs_status ON bet_legs(status)",
    "CREATE INDEX IF NOT EXISTS idx_bet_legs_sport ON bet_legs(sport)",
    "CREATE INDEX IF NOT EXISTS idx_bet_legs_game_status ON bet_legs(game_status)",
    "CREATE INDEX IF NOT EXISTS idx_bet_legs_player_id ON bet_legs(player_id)",
    "CREATE INDEX IF NOT EXISTS idx_bet_legs_date_status ON bet_legs(game_date, status)",
    "CREATE INDEX IF NOT EXISTS idx_bet_legs_sport_date ON bet_legs(sport, game_date)",
    "CREATE INDEX IF NOT EXISTS idx_bet_legs_bet_status ON bet_legs(bet_id, status)",
    
    # Teams table
    "CREATE INDEX IF NOT EXISTS idx_teams_team_name ON teams(team_name)",
    "CREATE INDEX IF NOT EXISTS idx_teams_sport ON teams(sport)",
    
    # Players table
    "CREATE INDEX IF NOT EXISTS idx_players_name_sport ON players(player_name, sport)",
    "CREATE INDEX IF NOT EXISTS idx_players_team_id ON players(team_id)",
    
    # Games table
    "CREATE INDEX IF NOT EXISTS idx_games_game_date ON games(game_date)",
    "CREATE INDEX IF NOT EXISTS idx_games_sport_date ON games(sport, game_date)",
    "CREATE INDEX IF NOT EXISTS idx_games_status ON games(status)",
]

def main():
    print(f"Connecting to production database...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    print(f"\nCreating {len(INDEXES)} indexes...")
    
    for i, index_sql in enumerate(INDEXES, 1):
        try:
            print(f"  [{i}/{len(INDEXES)}] {index_sql[:60]}...")
            cur.execute(index_sql)
            conn.commit()
            print(f"  ✅ Created")
        except Exception as e:
            print(f"  ⚠️  Error: {e}")
            conn.rollback()
    
    cur.close()
    conn.close()
    print(f"\n✅ Finished creating indexes!")

if __name__ == '__main__':
    main()
