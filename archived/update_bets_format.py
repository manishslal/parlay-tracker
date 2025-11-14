#!/usr/bin/env python3
"""
Script to update bet JSON files with new fields and compact format
- Adds 'bet_date' field (YYYY-MM-DD)
- Adds 'status' field (Won/Loss for historical, empty for live/today)
- Calculates status based on leg outcomes
- Outputs compact JSON (no indentation)
"""

import json
from helpers.bet_parser import calculate_bet_status, extract_bet_date

def update_historical_bets(input_file: str, output_file: str):
    """Update historical bets with new fields"""
    print(f"Updating {input_file}...")
    
    with open(input_file, 'r') as f:
        bets = json.load(f)
    
    updated_count = 0
    for bet in bets:
        # Add bet_date if not present
        if 'bet_date' not in bet:
            bet['bet_date'] = extract_bet_date(bet)
            updated_count += 1
        
        # Add status if not present (for historical bets)
        if 'status' not in bet:
            bet['status'] = calculate_bet_status(bet)
            updated_count += 1
    
    # Write compact JSON (no indentation)
    with open(output_file, 'w') as f:
        json.dump(bets, f, separators=(',', ':'))
    
    print(f"  ✓ Updated {len(bets)} bets ({updated_count} fields added)")
    print(f"  ✓ Saved compact JSON to {output_file}")

def update_live_or_today_bets(input_file: str, output_file: str):
    """Update live or today's bets with new fields"""
    print(f"Updating {input_file}...")
    
    try:
        with open(input_file, 'r') as f:
            bets = json.load(f)
    except FileNotFoundError:
        print(f"  ⚠ File not found, skipping")
        return
    
    updated_count = 0
    for bet in bets:
        # Add bet_date if not present
        if 'bet_date' not in bet:
            bet['bet_date'] = extract_bet_date(bet)
            updated_count += 1
        
        # Add empty status for live/today bets
        if 'status' not in bet:
            bet['status'] = ""
            updated_count += 1
    
    # Write compact JSON (no indentation)
    with open(output_file, 'w') as f:
        json.dump(bets, f, separators=(',', ':'))
    
    print(f"  ✓ Updated {len(bets)} bets ({updated_count} fields added)")
    print(f"  ✓ Saved compact JSON to {output_file}")

def main():
    print("=" * 80)
    print("UPDATING BET JSON FILES WITH NEW FIELDS")
    print("=" * 80)
    print()
    
    # Update historical bets (with Won/Loss status)
    update_historical_bets(
        'data/Historical_Bets.json',
        'data/Historical_Bets.json'
    )
    print()
    
    # Update live bets (with empty status)
    update_live_or_today_bets(
        'data/Live_Bets.json',
        'data/Live_Bets.json'
    )
    print()
    
    # Update today's bets (with empty status)
    update_live_or_today_bets(
        'data/Todays_Bets.json',
        'data/Todays_Bets.json'
    )
    print()
    
    print("=" * 80)
    print("✅ ALL FILES UPDATED SUCCESSFULLY!")
    print("=" * 80)
    print()
    print("New fields added:")
    print("  - bet_date: YYYY-MM-DD format (extracted from game dates)")
    print("  - status: 'Won' or 'Loss' for historical, empty for live/today")
    print()
    print("Files are now in compact format (no indentation)")

if __name__ == "__main__":
    main()
