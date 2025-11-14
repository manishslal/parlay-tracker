import os
import sys
import psycopg2

# Clear Cowboys timestamp
DATABASE_URL = os.getenv('DATABASE_URL') or 'postgresql://parlays_user:wgEpC1q34LIekYv6uelYqSThFdoy8xJT@dpg-d43b4iripnbc73bmuv5g-a.virginia-postgres.render.com/parlays'

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Clear timestamp
    cur.execute("UPDATE teams SET last_stats_update = NULL WHERE team_abbr = 'DAL' AND sport = 'NFL'")
    conn.commit()
    print('✅ Cleared timestamp for Dallas Cowboys')
    
    conn.close()
    
    # Now run the update
    print('\n--- Running update_team_records.py ---\n')
    os.system('python3 update_team_records.py')
    
    # Check the results
    print('\n--- Checking Dallas Cowboys data ---\n')
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT team_name, wins, losses, ties, 
               division_rank, conference_rank, league_rank,
               playoff_seed, games_behind, streak,
               last_game_date, next_game_date
        FROM teams 
        WHERE team_abbr = 'DAL' AND sport = 'NFL'
    """)
    
    row = cur.fetchone()
    if row:
        print(f"Team: {row[0]}")
        print(f"Record: {row[1]}-{row[2]}-{row[3]}")
        print(f"Division Rank: {row[4]}")
        print(f"Conference Rank: {row[5]}")
        print(f"League Rank: {row[6]}")
        print(f"Playoff Seed: {row[7]}")
        print(f"Games Behind: {row[8]}")
        print(f"Streak: {row[9]}")
        print(f"Last Game: {row[10]}")
        print(f"Next Game: {row[11]}")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
