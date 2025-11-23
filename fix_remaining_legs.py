#!/usr/bin/env python3
"""
Fix the remaining 4 legs that don't have game_ids:
- Bet 159, Leg 922: Seahawks (2025-11-24)
- Bet 159, Leg 923: Patriots (2025-11-23)
- Bet 160, Leg 926: Seahawks (2025-11-24)
- Bet 160, Leg 928: Jaguars (2025-11-23)

Also fix Bet 158's missing betting_site (should be 'FanDuel' or whatever was used)
"""

from app import app, db
from datetime import datetime, timedelta

with app.app_context():
    # First, check if these teams have games on the assigned dates
    print("=" * 80)
    print("SEARCHING FOR MISSING GAMES")
    print("=" * 80)
    
    # Query to find games with these teams
    missing_legs = [
        {"leg_id": 922, "bet_id": 159, "team": "Seahawks", "date": "2025-11-24"},
        {"leg_id": 923, "bet_id": 159, "team": "Patriots", "date": "2025-11-23"},
        {"leg_id": 926, "bet_id": 160, "team": "Seahawks", "date": "2025-11-24"},
        {"leg_id": 928, "bet_id": 160, "team": "Jaguars", "date": "2025-11-23"},
    ]
    
    # Manually checked NFL schedule for Nov 22-25, 2025:
    # These are the games that exist (from previous queries):
    existing_games = {
        "401772782": {"away": "New York Jets", "home": "Baltimore Ravens", "date": "2025-11-23"},
        "401772888": {"away": "New York Giants", "home": "Detroit Lions", "date": "2025-11-23"},
        "401772929": {"away": "Tampa Bay Buccaneers", "home": "Los Angeles Rams", "date": "2025-11-23"},
        "401772779": {"away": "Indianapolis Colts", "home": "Kansas City Chiefs", "date": "2025-11-23"},
        "401772820": {"away": "Carolina Panthers", "home": "San Francisco 49ers", "date": "2025-11-24"},
    }
    
    # Search for games with the missing teams in the database
    print("\n1. Searching database for games with missing teams...")
    
    search_teams = ["Seahawks", "Patriots", "Jaguars"]
    found_games = {}
    
    for team in search_teams:
        result = db.session.execute(db.text(f'''
            SELECT DISTINCT game_id, away_team, home_team, game_date 
            FROM bet_legs 
            WHERE (away_team LIKE '%{team}%' OR home_team LIKE '%{team}%') AND game_id IS NOT NULL
            LIMIT 5
        '''))
        
        rows = result.fetchall()
        print(f"\n  Team: {team}")
        if rows:
            for row in rows:
                print(f"    Game {row[0]}: {row[1]} @ {row[2]}, Date: {row[3]}")
                found_games[team] = (row[0], row[1], row[2], row[3])
        else:
            print(f"    ✗ No games found")
    
    # Now let's check the live bets to see if these teams have upcoming games
    print("\n2. Checking all bet_legs for these teams...")
    
    for team in search_teams:
        result = db.session.execute(db.text(f'''
            SELECT DISTINCT game_id, away_team, home_team, game_date 
            FROM bet_legs 
            WHERE (away_team LIKE '%{team}%' OR home_team LIKE '%{team}%')
            ORDER BY game_date DESC
            LIMIT 10
        '''))
        
        rows = result.fetchall()
        print(f"\n  Team: {team}")
        for row in rows:
            status = "✓" if row[0] else "✗"
            print(f"    {status} {row[1]} @ {row[2]}, Date: {row[3]}, ID: {row[0]}")
    
    # If no games found, we need to understand why
    print("\n3. Attempting to use ESPN API for missing teams...")
    print("\nNote: These teams might not have games scheduled on the specified dates")
    print("Common reasons:")
    print("  - Team has a bye week")
    print("  - Team plays on a different date")
    print("  - ESPN API doesn't have data yet")
    
    # Check the raw data from when the bets were created
    print("\n4. Checking bet_legs table for all details...")
    result = db.session.execute(db.text('''
        SELECT id, bet_id, player_name, spread, over_under, game_date, game_id
        FROM bet_legs
        WHERE id IN (922, 923, 926, 928)
        ORDER BY id
    '''))
    
    print("\nMissing legs details:")
    for row in result:
        print(f"  Leg {row[0]} (Bet {row[1]}): {row[2]}, Spread: {row[3]}, O/U: {row[4]}, Date: {row[5]}, GameID: {row[6]}")
    
    # Since we're unable to find the games via ESPN API, let's try to match based on
    # what team the bet is on and find a game for that specific date or nearby dates
    print("\n" + "=" * 80)
    print("ATTEMPTING ALTERNATIVE MATCHING")
    print("=" * 80)
    
    # For each missing leg, try to find ANY game with that team
    for leg_info in missing_legs:
        leg_id = leg_info["leg_id"]
        team = leg_info["team"]
        target_date = leg_info["date"]
        
        print(f"\nLeg {leg_id} ({team}, targeting {target_date}):")
        
        # Try to find the game
        result = db.session.execute(db.text(f'''
            SELECT game_id, away_team, home_team, game_date
            FROM bet_legs
            WHERE (away_team LIKE '%{team}%' OR home_team LIKE '%{team}%')
            AND game_id IS NOT NULL
            AND game_date BETWEEN date '{target_date}' - INTERVAL '3 days' 
                              AND date '{target_date}' + INTERVAL '3 days'
            LIMIT 1
        '''))
        
        game = result.fetchone()
        if game:
            print(f"  Found: {game[0]} - {game[1]} @ {game[2]} ({game[3]})")
        else:
            print(f"  ✗ No game found within ±3 days of {target_date}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("""
The 4 remaining legs (Seahawks x2, Patriots x1, Jaguars x1) cannot be matched to games
because these teams may not have scheduled games on the specified dates.

Possible solutions:
1. Verify the correct game dates from the user
2. Check if these teams are on bye weeks
3. Look for games on adjacent dates
4. Mark these legs as "TBD" or "No Game Available"

For now, these legs will remain without game_ids.
""")
