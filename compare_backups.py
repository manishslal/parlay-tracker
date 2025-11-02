#!/usr/bin/env python3
"""
Check the main Historical_Bets.json file vs backup folder
"""
import json
import os

def compare_files():
    """Compare main file vs backup"""
    
    # Check main file
    main_file = 'data/Historical_Bets.json'
    backup_file = 'data/backup_20251101_011047/Historical_Bets.json'
    
    print("📊 COMPARING FILES\n")
    
    # Main file
    print(f"Main file: {main_file}")
    if os.path.exists(main_file):
        size = os.path.getsize(main_file)
        print(f"  Size: {size:,} bytes ({size/1024:.1f} KB)")
        
        with open(main_file, 'r') as f:
            main_data = json.load(f)
        print(f"  Bets: {len(main_data)}")
        
        # Check for ESPN data
        with_data = 0
        for bet in main_data[:10]:
            for leg in bet.get('legs', []):
                if 'current' in leg:
                    with_data += 1
                    break
        print(f"  First 10 with ESPN data: {with_data}")
        
        # Show example
        if main_data:
            print(f"\n  Example bet: {main_data[0].get('name')}")
            if main_data[0].get('legs'):
                leg = main_data[0]['legs'][0]
                print(f"    Player: {leg.get('player', 'N/A')}")
                print(f"    Has 'current': {'current' in leg}")
                if 'current' in leg:
                    print(f"    Current value: {leg['current']}")
    
    print(f"\n{'-'*70}\n")
    
    # Backup file
    print(f"Backup file: {backup_file}")
    if os.path.exists(backup_file):
        size = os.path.getsize(backup_file)
        print(f"  Size: {size:,} bytes ({size/1024:.1f} KB)")
        
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        print(f"  Bets: {len(backup_data)}")
        
        # Check for ESPN data
        with_data = 0
        for bet in backup_data[:10]:
            for leg in bet.get('legs', []):
                if 'current' in leg:
                    with_data += 1
                    break
        print(f"  First 10 with ESPN data: {with_data}")
        
        # Show example
        if backup_data:
            print(f"\n  Example bet: {backup_data[0].get('name')}")
            if backup_data[0].get('legs'):
                leg = backup_data[0]['legs'][0]
                print(f"    Player: {leg.get('player', 'N/A')}")
                print(f"    Has 'current': {'current' in leg}")
                if 'current' in leg:
                    print(f"    Current value: {leg['current']}")

if __name__ == '__main__':
    compare_files()
