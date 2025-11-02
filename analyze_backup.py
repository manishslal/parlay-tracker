#!/usr/bin/env python3
"""
Analyze which bets have ESPN data in Historical_Bets.json
"""
import json

def analyze_backup():
    """Show which bets have ESPN data"""
    
    backup_file = 'data/Historical_Bets.json'
    
    with open(backup_file, 'r') as f:
        data = json.load(f)
    
    print(f"📊 Analyzing {len(data)} bets in Historical_Bets.json\n")
    
    bets_with_data = []
    bets_without_data = []
    
    for bet in data:
        bet_name = bet.get('name', 'Unnamed')
        
        # Check if any leg has ESPN data (current field)
        has_data = False
        for leg in bet.get('legs', []):
            if 'current' in leg:
                has_data = True
                break
        
        if has_data:
            bets_with_data.append(bet_name)
        else:
            bets_without_data.append(bet_name)
    
    print(f"✅ Bets WITH ESPN data: {len(bets_with_data)} ({len(bets_with_data)/len(data)*100:.1f}%)")
    print(f"❌ Bets WITHOUT ESPN data: {len(bets_without_data)} ({len(bets_without_data)/len(data)*100:.1f}%)")
    
    print(f"\n{'='*70}")
    print("BETS WITH ESPN DATA (can be restored):")
    print('='*70)
    for i, name in enumerate(bets_with_data, 1):
        print(f"{i:2d}. {name}")
    
    print(f"\n{'='*70}")
    print("BETS WITHOUT ESPN DATA (cannot be restored from this file):")
    print('='*70)
    for i, name in enumerate(bets_without_data, 1):
        print(f"{i:2d}. {name}")
    
    print(f"\n{'='*70}")
    print("RECOMMENDATION:")
    print('='*70)
    if len(bets_with_data) > len(bets_without_data):
        print(f"✅ This file has ESPN data for {len(bets_with_data)} bets")
        print(f"   Run restore_espn_data.py to restore them to PostgreSQL")
        print(f"\n❌ {len(bets_without_data)} bets never had ESPN data collected")
        print(f"   These games are too old (ESPN API doesn't keep them)")
        print(f"   They will remain at 0% - nothing we can do")
    else:
        print(f"❌ Most bets don't have ESPN data in this file")
        print(f"   Need to find an older backup from when games were live")

if __name__ == '__main__':
    analyze_backup()
