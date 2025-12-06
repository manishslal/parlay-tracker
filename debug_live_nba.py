#!/usr/bin/env python3
"""Debug live NBA game data fetching for Ayton and White"""
import requests
import json
from datetime import datetime

# Test fetching today's NBA games
today = datetime.now().strftime('%Y-%m-%d')
print(f"Fetching NBA games for {today}...")

url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={datetime.now().strftime('%Y%m%d')}"
response = requests.get(url, timeout=10)
data = response.json()

events = data.get('events', [])
print(f"\nFound {len(events)} NBA games today\n")

# Find games with Deandre Ayton (Suns) or Derrick White (Celtics)
for event in events:
    comp = event['competitions'][0]
    teams = [c['team']['displayName'] for c in comp['competitors']]
    
    if 'Suns' in str(teams) or 'Celtics' in str(teams) or 'Phoenix' in str(teams) or 'Boston' in str(teams):
        print(f"=" * 70)
        print(f"Game: {event['name']}")
        print(f"Status: {event['status']['type']['name']}")
        print(f"Event ID: {event['id']}")
        
        # Fetch summary with boxscore
        summary_url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={event['id']}"
        summary = requests.get(summary_url, timeout=10).json()
        
        boxscore = summary.get('boxscore', {}).get('players', [])
        print(f"\nBoxscore teams found: {len(boxscore)}")
        
        # Look for Ayton and White
        for team_box in boxscore:
            team_name = team_box.get('team', {}).get('displayName', 'Unknown')
            print(f"\n  Team: {team_name}")
            
            stats = team_box.get('statistics', [])
            for cat in stats:
                cat_name = cat.get('name', 'NO_NAME')
                labels = cat.get('labels', [])
                
                # Look for REB label for rebounds
                if 'REB' in labels:
                    reb_idx = labels.index('REB')
                    print(f"    Category: '{cat_name}' - Labels: {labels}")
                    
                    # Check for Ayton and White
                    for athlete in cat.get('athletes', []):
                        name = athlete.get('athlete', {}).get('displayName', 'Unknown')
                        stats_data = athlete.get('stats', [])
                        
                        if 'Ayton' in name or 'White' in name:
                            print(f"      ✅ FOUND {name}")
                            print(f"         Stats: {stats_data}")
                            if reb_idx < len(stats_data):
                                print(f"         Rebounds (REB): {stats_data[reb_idx]}")
                
                # Look for 3PT label for three-pointers
                if '3PT' in labels:
                    three_idx = labels.index('3PT')
                    print(f"    Category: '{cat_name}' - Labels: {labels}")
                    
                    for athlete in cat.get('athletes', []):
                        name = athlete.get('athlete', {}).get('displayName', 'Unknown')
                        stats_data = athlete.get('stats', [])
                        
                        if 'Ayton' in name or 'White' in name:
                            print(f"      ✅ FOUND {name}")
                            print(f"         Stats: {stats_data}")
                            if three_idx < len(stats_data):
                                print(f"         3-Pointers (3PT): {stats_data[three_idx]}")

print("\n" + "=" * 70)
