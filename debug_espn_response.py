from helpers.utils import get_events
import json
import datetime

def debug_espn():
    today = "2025-11-24"
    print(f"Fetching NBA events for {today}...")
    events = get_events(today, sport='NBA')
    
    print(f"Found {len(events)} events.")
    
    target_game = None
    for event in events:
        name = event['name']
        print(f"Checking event: {name}")
        if "Warriors" in name or "Jazz" in name:
            target_game = event
            break
            
    if not target_game:
        print("Warriors vs Jazz game not found.")
        return

    print(f"\nAnalyzing game: {target_game['name']}")
    
    # Get boxscore from summary endpoint as the main app does
    import requests
    summary_url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={target_game['id']}"
    print(f"Fetching summary from: {summary_url}")
    summary = requests.get(summary_url).json()
    
    boxscore = summary.get("boxscore", {})
    players = boxscore.get("players", [])
    
    print(f"\nBoxscore Players Data (First Team):")
    if players:
        team1 = players[0]
        print(f"Team: {team1.get('team', {}).get('displayName')}")
        
        # Print available categories
        print("Categories found:")
        for cat in team1.get("statistics", []):
            print(f" - Name: '{cat.get('name')}'")
            print(f"   Labels: {cat.get('labels')}")
            
            # Check Stephen Curry stats if in this team
            for athlete in cat.get("athletes", []):
                name = athlete.get("athlete", {}).get("displayName")
                if "Curry" in name:
                    print(f"   -> Found {name} stats: {athlete.get('stats')}")

if __name__ == "__main__":
    debug_espn()
