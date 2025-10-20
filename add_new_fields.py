#!/usr/bin/env python3
"""
Script to add betting_site and bet_id fields to all parlays in JSON files.
"""

import json
import os

DATA_DIR = "./Data"

def add_new_fields(parlay):
    """Add betting_site and bet_id fields if they don't exist."""
    # Maintain field order: name, type, odds, wager, returns, betting_site, bet_id, legs
    result = {
        "name": parlay.get("name", "Unknown Bet"),
        "type": parlay.get("type", "Wager")
    }
    
    # Add existing betting fields
    result["odds"] = parlay.get("odds", "")
    result["wager"] = parlay.get("wager", "")
    
    # Handle returns - convert None/null to empty string
    returns = parlay.get("returns", "")
    result["returns"] = "" if returns is None else returns
    
    # Add new fields with empty string defaults
    result["betting_site"] = parlay.get("betting_site", "")
    result["bet_id"] = parlay.get("bet_id", "")
    
    # Keep legs
    result["legs"] = parlay.get("legs", [])
    
    return result

def update_file(filepath):
    """Add new fields to all parlays in a file."""
    print(f"Updating {filepath}...")
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print(f"  ⚠️  {filepath} is not a list, skipping")
            return
        
        # Update each parlay
        updated_data = [add_new_fields(parlay) for parlay in data]
        
        # Write back with proper formatting
        with open(filepath, 'w') as f:
            json.dump(updated_data, f, indent=4)
        
        print(f"  ✅ Updated {len(updated_data)} parlays")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")

def main():
    print("🔧 Adding betting_site and bet_id fields to all parlays...")
    print()
    
    files_to_update = [
        "Todays_Bets.json",
        "Live_Bets.json", 
        "Historical_Bets.json",
        "sample_Bets.json"
    ]
    
    for filename in files_to_update:
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            update_file(filepath)
        else:
            print(f"⚠️  {filepath} not found, skipping")
    
    print()
    print("✨ Update complete!")
    print()
    print("📊 File sizes:")
    os.system(f"wc -l {DATA_DIR}/*.json")

if __name__ == "__main__":
    main()
