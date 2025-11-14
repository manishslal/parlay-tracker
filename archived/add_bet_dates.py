#!/usr/bin/env python3
"""
Script to add 'bet_date' field to all JSON files.

For historical bets:
- Uses the earliest game_date from legs minus 1 day as the bet_date
- This assumes bets are typically placed before games start

For current/live bets:
- Uses today's date or the earliest game_date minus 1 day
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

def get_earliest_game_date(legs):
    """Extract the earliest game_date from legs."""
    if not legs:
        return None
    
    dates = []
    for leg in legs:
        game_date = leg.get('game_date')
        if game_date:
            try:
                dates.append(datetime.strptime(game_date, '%Y-%m-%d'))
            except ValueError:
                continue
    
    return min(dates) if dates else None

def derive_bet_date(bet):
    """
    Derive a reasonable bet_date for a bet.
    Uses earliest game_date minus 1 day.
    """
    legs = bet.get('legs', [])
    earliest_game = get_earliest_game_date(legs)
    
    if earliest_game:
        # Assume bet was placed 1 day before the first game
        bet_date = earliest_game - timedelta(days=1)
        return bet_date.strftime('%Y-%m-%d')
    
    # Fallback to current date if no game_date found
    return datetime.now().strftime('%Y-%m-%d')

def add_bet_dates_to_file(file_path, is_historical=False):
    """Add bet_date field to all bets in a JSON file."""
    print(f"\nProcessing {file_path}...")
    
    if not Path(file_path).exists():
        print(f"  ⚠️  File not found: {file_path}")
        return
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        print(f"  ⚠️  Expected list, got {type(data)}")
        return
    
    modified_count = 0
    for bet in data:
        # Skip if bet_date already exists
        if 'bet_date' in bet:
            continue
        
        # Add bet_date
        bet['bet_date'] = derive_bet_date(bet)
        modified_count += 1
    
    # Save back to file with proper formatting
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"  ✅ Added bet_date to {modified_count} bets")
    print(f"  📊 Total bets in file: {len(data)}")

def main():
    """Main function to process all JSON files."""
    print("=" * 60)
    print("Adding bet_date field to all JSON files")
    print("=" * 60)
    
    base_path = Path(__file__).parent / "Data"
    
    # Process each file
    files = [
        (base_path / "Historical_Bets.json", True),
        (base_path / "Live_Bets.json", False),
        (base_path / "Todays_Bets.json", False),
    ]
    
    for file_path, is_historical in files:
        add_bet_dates_to_file(str(file_path), is_historical)
    
    print("\n" + "=" * 60)
    print("✅ All files processed successfully!")
    print("=" * 60)
    
    # Show a sample bet from Historical_Bets.json
    print("\nSample bet from Historical_Bets.json:")
    with open(base_path / "Historical_Bets.json", 'r') as f:
        data = json.load(f)
        if data:
            sample = data[0]
            print(f"  Name: {sample.get('name')}")
            print(f"  Bet Date: {sample.get('bet_date')}")
            print(f"  Game Date (first leg): {sample.get('legs', [{}])[0].get('game_date', 'N/A')}")

if __name__ == '__main__':
    main()
