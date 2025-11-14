#!/usr/bin/env python3
"""
Test the new to_dict_structured() method
Compare it with the old to_dict() method
"""
from app import app, db
from models import Bet
import json

def test_structured_dict():
    with app.app_context():
        # Get a bet with legs
        bet = Bet.query.filter(Bet.total_legs > 0).first()
        
        if not bet:
            print("❌ No bets found with legs")
            return
        
        print("=" * 80)
        print(f"Testing Bet ID: {bet.id}")
        print("=" * 80)
        
        # Get old JSON blob version
        print("\n📦 OLD METHOD (to_dict - from JSON blob):")
        print("-" * 80)
        old_dict = bet.to_dict()
        print(f"Name: {old_dict.get('name')}")
        print(f"Type: {old_dict.get('type')}")
        print(f"Wager: ${old_dict.get('wager')}")
        print(f"Odds: {old_dict.get('odds')}")
        print(f"Returns: ${old_dict.get('returns')}")
        print(f"Legs: {len(old_dict.get('legs', []))}")
        
        if old_dict.get('legs'):
            print("\nFirst leg:")
            leg = old_dict['legs'][0]
            print(f"  Player: {leg.get('player')}")
            print(f"  Team: {leg.get('team')}")
            print(f"  Position: {leg.get('position')}")
            print(f"  Jersey: {leg.get('jersey_number', 'N/A')}")
            print(f"  Stat: {leg.get('stat')}")
            print(f"  Target: {leg.get('target')}")
            print(f"  Status: {leg.get('status')}")
        
        # Get new structured version
        print("\n🗃️  NEW METHOD (to_dict_structured - from database tables):")
        print("-" * 80)
        try:
            new_dict = bet.to_dict_structured()
            print(f"Name: {new_dict.get('name')}")
            print(f"Type: {new_dict.get('type')}")
            print(f"Wager: ${new_dict.get('wager')}")
            print(f"Odds: {new_dict.get('odds')}")
            print(f"Returns: ${new_dict.get('returns')}")
            print(f"Legs: {len(new_dict.get('legs', []))}")
            
            if new_dict.get('legs'):
                print("\nFirst leg:")
                leg = new_dict['legs'][0]
                print(f"  Player: {leg.get('player')}")
                print(f"  Team: {leg.get('team')}")
                print(f"  Position: {leg.get('position')}")
                print(f"  Jersey: #{leg.get('jersey_number', 'N/A')}")
                print(f"  Team Abbr: {leg.get('team_abbr', 'N/A')}")
                print(f"  Stat: {leg.get('stat')}")
                print(f"  Target: {leg.get('target')}")
                print(f"  Status: {leg.get('status')}")
                print(f"  Opponent: {leg.get('opponent')}")
            
            print("\n✅ NEW METHOD WORKS!")
            
            # Compare leg counts
            old_legs = len(old_dict.get('legs', []))
            new_legs = len(new_dict.get('legs', []))
            
            if old_legs == new_legs:
                print(f"\n✅ Leg count matches: {old_legs} legs")
            else:
                print(f"\n⚠️  Leg count mismatch: OLD={old_legs}, NEW={new_legs}")
            
            # Show all players with jersey numbers
            print("\n👕 Players with Jersey Numbers:")
            print("-" * 80)
            for i, leg in enumerate(new_dict.get('legs', []), 1):
                jersey = f"#{leg.get('jersey_number')}" if leg.get('jersey_number') else "N/A"
                team = leg.get('team_abbr', leg.get('team', 'N/A'))
                print(f"{i:2}. {leg.get('player'):25} {team:4} {jersey:5} {leg.get('position', 'N/A'):3}")
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 80)

if __name__ == "__main__":
    test_structured_dict()
