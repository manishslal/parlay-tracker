#!/usr/bin/env python3
"""
Cleanup script to remove 'games' key from parlay JSON files.
Restores files to their original simple format with only parlay metadata and legs.
"""

import json
import os

DATA_DIR = "./data"

def cleanup_parlay(parlay):
    """Remove 'games' key and 'current' from legs, keep only essential fields."""
    cleaned = {
        "name": parlay.get("name", "Unknown Bet"),
        "type": parlay.get("type", "Wager")
    }
    
    # Always add betting fields (use existing values or default to empty string)
    cleaned["odds"] = parlay.get("odds", "")
    cleaned["wager"] = parlay.get("wager", "")
    
    # Handle returns - convert None/null to empty string
    returns = parlay.get("returns", "")
    cleaned["returns"] = "" if returns is None else returns
    
    # Add legs array
    cleaned["legs"] = []
    
    # Clean up legs - remove 'current', 'parlay_name', keep essential fields
    for leg in parlay.get("legs", []):
        cleaned_leg = {
            "game_date": leg.get("game_date"),
            "away": leg.get("away"),
            "home": leg.get("home"),
            "player": leg.get("player"),
            "target": leg.get("target"),
            "stat": leg.get("stat")
        }
        
        # Add optional leg fields if they exist
        if "odds" in leg:
            cleaned_leg["odds"] = leg["odds"]
            
        cleaned["legs"].append(cleaned_leg)
    
    return cleaned

def cleanup_file(filepath):
    """Clean up a single JSON file."""
    print(f"Cleaning up {filepath}...")
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print(f"  ⚠️  {filepath} is not a list, skipping")
            return
        
        # Clean each parlay
        cleaned_data = [cleanup_parlay(parlay) for parlay in data]
        
        # Write back with proper formatting
        with open(filepath, 'w') as f:
            json.dump(cleaned_data, f, indent=4)
        
        print(f"  ✅ Cleaned {len(cleaned_data)} parlays")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")

def main():
    print("🧹 Cleaning up JSON files...")
    print()
    
    files_to_clean = [
        "Todays_Bets.json",
        "Live_Bets.json", 
        "Historical_Bets.json"
    ]
    
    for filename in files_to_clean:
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            cleanup_file(filepath)
        else:
            print(f"⚠️  {filepath} not found, skipping")
    
    print()
    print("✨ Cleanup complete!")
    print()
    print("📊 Line counts:")
    os.system(f"wc -l {DATA_DIR}/*.json")

if __name__ == "__main__":
    main()
