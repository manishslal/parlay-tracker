#!/usr/bin/env python3
"""
Comprehensive test to check why live data isn't being fetched
Tests the full flow: database -> endpoint -> ESPN API -> response
"""
import requests
import json
from datetime import datetime

# Production database connection
DATABASE_URL = 'postgresql://parlays_user:wgEpC1q34LIekYv6uelYqSThFdoy8xJT@dpg-d43b4iripnbc73bmuv5g-a.virginia-postgres.render.com/parlays'

def check_database_bets():
    """Check what bets are actually in the database"""
    import psycopg2
    
    print("=" * 70)
    print("STEP 1: Checking Database Bets")
    print("=" * 70)
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Check all bets
    cur.execute("""
        SELECT id, status, is_active, created_at
        FROM bets
        ORDER BY created_at DESC
        LIMIT 10
    """)
    
    bets = cur.fetchall()
    print(f"\nFound {len(bets)} recent bets:")
    for bet in bets:
        print(f"  ID: {bet[0]}, Status: {bet[1]}, Active: {bet[2]}, Created: {bet[3]}")
    
    # Check for Ayton legs
    cur.execute("""
        SELECT bl.id, bl.bet_id, bl.player_name, bl.stat_type, bl.target_value, 
               bl.achieved_value, bl.status, bl.game_status, bl.sport
        FROM bet_legs bl
        WHERE bl.player_name ILIKE '%ayton%'
        ORDER BY bl.id DESC
        LIMIT 5
    """)
    
    ayton_legs = cur.fetchall()
    print(f"\nAyton legs found: {len(ayton_legs)}")
    for leg in ayton_legs:
        print(f"  Leg ID: {leg[0]}, Bet: {leg[1]}, Player: {leg[2]}")
        print(f"    Stat: {leg[3]}, Target: {leg[4]}, Achieved: {leg[5]}")
        print(f"    Status: {leg[6]}, Game Status: {leg[7]}, Sport: {leg[8]}")
    
    cur.close()
    conn.close()
    
    return bets, ayton_legs

def test_stats_endpoint():
    """Test the /stats endpoint directly"""
    print("\n" + "=" * 70)
    print("STEP 2: Testing /stats Endpoint")
    print("=" * 70)
    
    # You'll need to provide the admin token
    admin_token = input("\nEnter ADMIN_API_KEY (from .env file): ").strip()
    
    url = "https://parlay-tracker-backend.onrender.com/stats"
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    print(f"\nCalling: {url}")
    response = requests.get(url, headers=headers, timeout=30)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Returned {len(data)} bets")
        
        # Check for Ayton
        for bet in data:
            for leg in bet.get('legs', []):
                if 'ayton' in leg.get('player', '').lower():
                    print(f"\n✅ Found Ayton leg:")
                    print(f"  Player: {leg.get('player')}")
                    print(f"  Stat: {leg.get('stat')}")
                    print(f"  Current: {leg.get('current')}")
                    print(f"  Target: {leg.get('target')}")
                    print(f"  Game Status: {leg.get('gameStatus')}")
                    print(f"  Sport: {leg.get('sport')}")
        
        return data
    else:
        print(f"ERROR: {response.text}")
        return None

def test_espn_direct():
    """Test ESPN API directly for today's NBA games"""
    print("\n" + "=" * 70)
    print("STEP 3: Testing ESPN API Directly")
    print("=" * 70)
    
    today = datetime.now().strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={today}"
    
    print(f"\nCalling: {url}")
    response = requests.get(url, timeout=10)
    data = response.json()
    
    events = data.get('events', [])
    print(f"Found {len(events)} NBA games today")
    
    # Find Lakers/Celtics game (Ayton is on Lakers)
    for event in events:
        name = event['name']
        if 'Lakers' in name or 'Celtics' in name:
            print(f"\n✅ Found game: {name}")
            print(f"   Status: {event['status']['type']['name']}")
            print(f"   Event ID: {event['id']}")

if __name__ == '__main__':
    print("DIAGNOSING LIVE DATA ISSUE")
    print("=" * 70)
    
    # Step 1: Check database
    bets, ayton_legs = check_database_bets()
    
    # Step 2: Test endpoint
    endpoint_data = test_stats_endpoint()
    
    # Step 3: Test ESPN
    test_espn_direct()
    
    print("\n" + "=" * 70)
    print("DIAGNOSIS COMPLETE")
    print("=" * 70)
