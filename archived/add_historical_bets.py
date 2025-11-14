#!/usr/bin/env python3
"""
Script to add historical bets to Historical_Bets.json
Parses bet data and looks up NFL matchups from ESPN API
"""

import json
from helpers.leg_parser import parse_legs_string
from helpers.bet_parser import (
    parse_bet_date,
    parse_betting_site,
    bet_exists,
    sort_historical_bets
)

def main():
    # Read existing historical bets
    historical_file = "Data/Historical_Bets.json"
    try:
        with open(historical_file, 'r') as f:
            historical_bets = json.load(f)
    except FileNotFoundError:
        historical_bets = []
    
    print(f"Current historical bets: {len(historical_bets)}")
    
    # Bet data from spreadsheet
    bet_data = [
        # Format: (date, bet_id, wager, odds, legs_text)
        ("9/4/25", "O/1368367/0000029", 10.00, 322, """Moneyline - Eagles (Y)
Anytime TD - Saquon Barkley (Y)
50+ Receiving Yds - A.J. Brown (N)
30+ Receiving Yds - DeVonta Smith (N)"""),
        
        ("9/4/25", "O/1368367/0000030", 5.00, 688, """100+ Rushing Yds - Saquon Barkley (N)
50+ Receiving Yds - George Pickens (N)
50+ Receiving Yds - CeeDee Lamb (Y)
3+ Receptions - Jake Ferguson (Y)
3+ Receptions - Dallas Goedert (Y)"""),
        
        ("9/4/25", "O/1368367/0000031", 5.00, 695, """100+ Rushing Yds - Saquon Barkley (N)
50+ Receiving Yds - George Pickens (N)
50+ Receiving Yds - CeeDee Lamb (Y)
3+ Receptions - Jake Ferguson (Y)
3+ Receptions - Dallas Goedert (Y)"""),
        
        ("9/4/25", "O/1368367/0000032", 10.00, 750, """5+ Rushing Yds in Each Qtr - Saquon Barkley (Y)
5+ Rushing Yds in Each Qtr - Javonte Williams (N)"""),
        
        ("9/4/25", "DK638926171300468480", 4.80, 380, """Anytime TD - A.J. Brown (N)
Anytime TD - Devonta Smith (N)"""),
        
        ("9/4/25", "DK638926174744164449", 5.00, 1200, """First TD Scorer - Saquon Barkley (N)"""),
        
        ("9/7/25", "O/0240915/0000029", 5.00, 509, """Anytime TD - Terry McLaurin (N)
25+ Receiving Yds - Terry McLaurin (Y)
50+ Receiving Yds - Malik Nabers (Y)
175+ Passing Yds - Jayden Daniels (Y)
Moneyline - Commanders (Y)"""),
        
        ("9/7/25", "O/0240915/0000030", 5.00, 247, """40+ Receiving Yds - Terry McLaurin (N)
50+ Receiving Yds - Malik Nabers (Y)
175+ Passing Yds - Jayden Daniels (Y)
175+ Passing Yds - Russel Wilson (N)
Moneyline - Commanders (Y)"""),
        
        ("9/7/25", "O/0240915/0000033", 10.00, 210, """Anytime TD - Lamar Jackson (Y)"""),
        
        ("9/7/25", "O/0240915/0000032", 10.00, -105, """Anytime TD - Josh Allen (Y)"""),
        
        ("9/7/25", "O/0240915/0000031", 10.00, 501, """200+ Passing Yds - Josh Allen (Y)
225+ Passing & Rushing Yds - Lamar Jackson (Y)
30+ Receiving Yds - Zay Flowers (Y)
25+ Receiving Yds - Khalil Shakir (Y)
Anytime TD - James Cook (Y)"""),
        
        ("9/7/25", "O/0240915/0000036", 10.00, 423, """2+ Passing TDs - Josh Allen (Y)
3+ Receptions - Dalton Kincaid (Y)
Anytime TD - Dalton Kincaid (Y)"""),
        
        ("9/7/25", "O/0240915/0000034", 5.00, -122, """Over 1.5 Passing TDs - Lamar Jackson (Y)"""),
        
        ("9/7/25", "O/0240915/0000035", 10.00, 159, """Anytime TD - Derrick Henry (Y)
4+ Receptions - Mark Andrews (N)"""),
        
        ("9/8/25", "O/0240915/0000037", 5.00, 297, """Anytime TD - Aaron Jones (Y)
40+ Rushing Yds - Aaron Jones (N)
2+ Receptions - Aaron Jones (Y)"""),
        
        ("9/8/25", "O/0240915/0000038", 5.00, 297, """Anytime TD - Aaron Jones (Y)
40+ Rushing Yds - Aaron Jones (N)
2+ Receptions - Aaron Jones (Y)"""),
        
        ("9/8/25", "O/0240915/0000039", 10.00, 2746, """Anytime TD - Aaron Jones (Y)
Anytime TD - D'Andre Swift (N)
Anytime TD - T.J. Hockenson (N)"""),
        
        ("9/8/25", "DK638929734797786019", 4.80, 355, """Anytime TD - Justin Jefferson (Y)
180+ Passing Yds - J.J. McCarthy (Y)
170+ Passing Yds - Caleb Williams (Y)
60+ Receiving Yds - Justin Jefferson (Y)
25+ Receiving Yds - T.J. Hockenson (Y)"""),
        
        ("9/8/25", "DK638929693228150392", 10.00, 2500, """Moneyline - Bears (N)
Anytime TD - D'Andre Swift (N)
Anytime TD - Aaron Jones (Y)
50+ Receiving Yds - Justin Jefferson (Y)
50+ Receiving Yds - D.J. Moore (N)"""),
        
        ("9/11/25", "DK638932329442198194", 10.00, 800, """Moneyline - Commanders (N)
Anytime TD - Tucker Kraft (Y)"""),
        
        ("9/14/25", "O/0240915/0000041", 10.00, 431, """Anytime TD - Kyren Williams (N)
Anytime TD - Derrick Henry (N)
Anytime TD - James Cook (Y)"""),
        
        ("9/15/25", "O/0240915/0000042", 10.00, 631, """200+ Passing Yds - Geno Smith (N)
200+ Passing Yds - Justin Herbert (Y)
Anytime TD - Jakobi Meyers (N)
4+ Receptions - Keenan Allen (Y)
Over 1.5 Passing TDs - Justin Herbert (Y)"""),
        
        ("9/15/25", "O/0240915/0000043", 10.00, 152, """Moneyline - Raiders (N)"""),
        
        ("9/15/25", "O/0240915/0000040", 10.00, 452, """Moneyline - Cowboys (Y)
Moneyline - Bengals (Y)
Moneyline - Ravens (Y)
Moneyline - Chargers (Y)
Moneyline - Bills (Y)"""),
        
        ("9/18/25", "O/1368367/0000033", 10.00, -116, """Moneyline - Bills (Y)
Anytime TD - Josh Allen (N)"""),
        
        ("9/21/25", "O/0240915/0000044", 10.00, 325, """Moneyline - Chiefs (Y)
2+ Passing TDs - Patrick Mahomes (N)
50+ Receiving Yds - Malik Nabers (N)
150+ Passing Yds - Russell Wilson (Y)
175+ Passing Yds - Patrick Mahomes (Y)"""),
        
        ("9/21/25", "O/1119460/0000003", 10.00, 1053, """Moneyline - Eagles (Y)
Moneyline - Buccaneers (Y)
Moneyline - Packers (N)
Moneyline - Falcons (N)
Moneyline - Colts (Y)
Moneyline - Steelers (Y)"""),
        
        ("9/21/25", "O/1119460/0000002", 10.00, 1039, """Moneyline - Eagles (Y)
Moneyline - Buccaneers (Y)
Moneyline - Packers (N)
Moneyline - Falcons (N)
Moneyline - Colts (Y)
Moneyline - Commanders (Y)"""),
        
        ("9/21/25", "DK638940702867776036", 10.00, 1266, """Anytime TD - Christian McCaffrey (N)
Anytime TD - Bucky Irving (N)
Anytime TD - Bijan Robinson (N)
Anytime TD - Jordan Mason (Y)
Anytime TD - Kenneth Walker III (Y)"""),
        
        ("9/22/25", "DK638941829591667808", 10.00, 230, """Anytime TD - Amon-Ra St. Brown (Y)
Anytime TD - Derrick Henry (Y)"""),
        
        ("9/22/25", "O/0240915/0000045", 10.00, 294, """Moneyline - Ravens (N)
200+ Passing Yds - Jared Goff (Y)
225+ Passing & Rushing Yds - Lamar Jackson (Y)
40+ Receiving Yds - Zay Flowers (N)
40+ Receiving Yds - Sam LaPorta (Y)"""),
        
        ("9/25/25", "O/0240915/0000046", 10.00, 1018, """200+ Passing Yds - Kyler Murray (Y)
2+ Passing TDs - Sam Darnold (N)
50+ Rushing Yds - Trey Benson (N)
6+ Receptions - Jaxon Smith-Njigba (N)"""),
        
        ("9/25/25", "O/0240915/0000047", 10.00, -105, """150+ Passing Yds - Kyler Murray (Y)
25+ Receiving Yds - Marvin Harrison Jr. (Y)
25+ Receiving Yds - Trey McBride (Y)
5+ Receiving Yds - Michael Wilson (Y)
2+ Receptions - Trey Benson (Y)"""),
        
        ("9/25/25", "DK638944245376940359", 10.00, 800, """Anytime TD - Trey McBride (N)
Anytime TD - Zach Charbonnet (Y)
15+ Receiving Yds - Marvin Harrison Jr. (Y)"""),
        
        ("9/25/25", "DK638944230797523015", 10.00, 240, """80+ Receiving Yds - Jaxon Smith-Njigba (N)
40+ Receiving Yds - Trey McBride (Y)
25+ Rushing Yds - Kyler Murray (Y)"""),
        
        ("9/28/25", "DK638946706562465944", 20.00, 391, """Moneyline - Lions (Y)
Moneyline - Bills (Y)
Moneyline - Broncos (Y)
Moneyline - Chargers (N)
Moneyline - Packers (Y)
Moneyline - Ravens (N)"""),
        
        ("9/28/25", "DK638946708311633880", 20.00, 488, """Moneyline - Lions (Y)
Moneyline - Bills (Y)
Moneyline - Broncos (Y)
Moneyline - Chargers (N)
Moneyline - Packers (Y)
Moneyline - Chiefs (Y)"""),
        
        ("9/28/25", "DK638946864775833794", 5.00, 238, """200+ Passing Yds - Matthew Stafford (Y)
180+ Passing Yds - Daniel Jones (Y)
6+ Receptions - Puka Nacua (Y)
60+ Rushing Yds - Jonathan Taylor (Y)
40+ Receiving Yds - Davante Adams (Y)
25+ Receiving Yds - Michael Pittman Jr. (Y)"""),
        
        ("9/28/25", "O/0240915/0000048", 10.00, 602, """Over 44.5 Total Points - Eagles vs Buccaneers (Y)
70+ Rushing Yds - Omarion Hampton (Y)
Anytime TD - James Cook (Y)
3+ Receptions - Sam LaPorta (Y)"""),
        
        ("9/28/25", "O/0240915/0000049", 20.00, -110, """150+ Passing Yds - Spencer Rattler (N)
3+ Receptions - DeVonta Smith (N)
2+ Receptions - Bucky Irving (Y)
25+ Rushing Yds - David Montgomery (N)"""),
        
        ("9/28/25", "O/0240915/0000050", 10.00, 208, """200+ Passing Yds - Jordan Love (Y)
60+ Receiving Yds - George Pickens (Y)"""),
        
        ("10/2/25", "O/0240915/0000051", 10.00, 481, """Moneyline - Rams (N)
200+ Passing Yds - Matthew Stafford (Y)
175+ Passing Yds - Mac Jones (Y)
Anytime TD - Christian McCaffrey (Y)
30+ Receiving Yds - Davante Adams (Y)"""),
        
        ("10/2/25", "DK638950461471078613", 20.00, 174, """200+ Passing Yds - Matthew Stafford (Y)
170+ Passing Yds - Mac Jones (Y)
70+ Receiving Yds - Puka Nacua (Y)
25+ Receiving Yds - Christian McCaffrey (Y)
40+ Rushing Yds - Christian McCaffrey (Y)"""),
        
        ("10/5/25", "DK638952803155496376", 10.00, 869, """Moneyline - Dolphins (N)
Moneyline - Texans (Y)
Moneyline - Colts (Y)
Moneyline - Giants (N)"""),
        
        ("10/5/25", "DK638953058013659823", 10.00, 111, """Anytime TD - Josh Allen (N)"""),
        
        ("10/5/25", "O/1368367/0000034", 10.00, 323, """150+ Passing Yds - Jalen Hurts (Y)
150+ Passing Yds - Bo Nix (N)
60+ Rushing Yds - Saquon Barkley (Y)
Anytime TD - Saquon Barkley (Y)"""),
        
        ("10/5/25", "O/0240915/0000052", 10.00, 402, """200+ Passing Yds - Josh Allen (Y)
200+ Passing Yds - Drake Maye (Y)
70+ Rushing & Receiving Yds - James Cook (N)
25+ Receiving Yds - Stefon Diggs (Y)
Anytime TD - James Cook (N)"""),
        
        ("10/6/25", "DK638953925568002478", 10.00, 375, """Over 27.5 Receiving Yds - Dyami Brown (N)
Over 1.5 Passing TDs - Patrick Mahomes (N)
Over 26.5 Rushing Yds - Isiah Pacheco (Y)"""),
        
        ("10/6/25", "O/0240915/0000054", 10.00, 217, """200+ Passing Yds - Patrick Mahomes (Y)
175+ Passing Yds - Trevor Lawrence (Y)
30+ Receiving Yds - Xavier Worthy (Y)
25+ Receiving Yds - Travis Kelce (Y)
15+ Receiving Yds - Isiah Pacheco (Y)"""),
        
        ("10/6/25", "O/0240915/0000053", 5.00, 1699, """200+ Passing Yds - Patrick Mahomes (Y)
175+ Passing Yds - Trevor Lawrence (Y)
30+ Receiving Yds - Xavier Worthy (Y)
20+ Receiving Yds - Travis Kelce (Y)
20+ Receiving Yds - Marquise Brown (Y)
15+ Receiving Yds - Travis Hunter (Y)
15+ Rushing Yds - Isiah Pacheco (Y)
10+ Rushing Yds - Patrick Mahomes (Y)
40+ Rushing Yds - Travis Etienne (Y)
Anytime TD - Travis Etienne (N)"""),
        
        ("10/12/25", "O/1368367/0000035", 5.00, 3088, """Moneyline - Broncos (N)
Moneyline - Rams (N)
Moneyline - Cardinals (N)
Moneyline - Chargers (N)
Moneyline - Texans (N)
Moneyline - Ravens (N)"""),
        
        ("10/12/25", "O/1368367/0000036", 10.00, 979, """Moneyline - Cowboys (N)
Moneyline - Chargers (Y)
Moneyline - Rams (Y)
Moneyline - Steelers (Y)
Moneyline - Colts (Y)
Moneyline - Jaguars (N)"""),
        
        ("10/12/25", "O/0240915/0000055", 5.00, 863, """Anytime TD - Travis Kelce (N)
20+ Rushing Yds - Patrick Mahomes (Y)
Anytime TD - Amon-Ra St. Brown (N)
Over 1.5 Passing TDs - Patrick Mahomes (Y)"""),
        
        ("10/12/25", "DK638959109257988077", 5.00, 10400, """Under 268.5 Passing Yds - Patrick Mahomes (Y)
Anytime TD - Travis Kelce (N)
15+ Rushing Yds - Jared Goff (N)
Anytime TD - Jahmyr Gibbs (N)"""),
        
        ("10/13/25", "DK638959876709085359", 10.00, 656, """3+ Receptions - Bijan Robinson (Y)
80+ Rushing & Receiving Yds - Bijan Robinson (Y)
Anytime TD - Tyler Allgeier (Y)
60+ Receiving Yds - Drake London (Y)"""),
        
        ("10/13/25", "DK638959884125024982", 10.00, 765, """Anytime TD - Dalton Kincaid (N)
Anytime TD - Josh Allen (N)"""),
        
        ("10/13/25", "DK638959890786574108", 10.00, 516, """80+ Rushing Yds - Roschon Johnson (N)
Anytime TD - Roschon Johnson (N)
200+ Passing Yds - Caleb Williams (Y)
3+ Receptions - Zach Ertz (Y)"""),
        
        ("10/13/25", "O/0240915/0000056", 10.00, 193, """80+ Rushing Yds - Bijan Robinson (Y)
Anytime TD - Bijan Robinson (Y)
3+ Receptions - Bijan Robinson (Y)
60+ Receiving Yds - Drake London (Y)"""),
        
        ("10/13/25", "O/0240915/0000057", 10.00, 303, """Anytime TD - Khalil Shakir (N)
Over 20.5 Longest Reception - Khalil Shakir (N)"""),
        
        ("10/13/25", "O/1368367/0000037", 10.00, 286, """2+ TDs - Drake London (N)"""),
        
        ("10/16/25", "O/0240915/0000058", 10.00, 452, """175+ Passing Yds - Aaron Rodgers (Y)
200+ Passing Yds - Joe Flacco (Y)
2+ Passing TDs - Aaron Rodgers (Y)
60+ Receiving Yds - Ja'Marr Chase (Y)
60+ Receiving Yds - DK Metcalf (N)
10+ Receiving Yds - Jaylen Warren (Y)"""),
        
        ("10/16/25", "DK638962542882998573", 10.00, 1145, """Spread -11.5 - Chiefs (Y)
Spread -5.5 - Steelers (N)
Spread -7 - Patriots (Y)
Moneyline - Commanders (N)"""),
        
        ("10/19/25", "DK638964901122094929", 10.00, 1543, """Anytime TD - A.J. Brown (Y)
Anytime TD - Saquon Barkley (N)
Anytime TD - Rome Odunze (N)"""),
        
        ("10/19/25", "DK638965142909383818", 10.00, 397, """Anytime TD - Bijan Robinson (Y)
200+ Passing Yds - Mac Jones (N)
180+ Passing Yds - Michael Penix Jr. (Y)
1+ Passing TDs - Michael Penix Jr. (Y)
50+ Receiving Yds - Drake London (N)
90+ Rushing & Receiving Yds - Bijan Robinson (Y)
40+ Rushing Yds - Christian McCaffrey (Y)"""),
        
        ("10/19/25", "O/1368367/0000038", 10.00, 720, """Moneyline - Chiefs (Y)
Moneyline - Bears (Y)
Moneyline - Panthers (Y)
Moneyline - Patriots (Y)
Spread +2.5 - Vikings (N)"""),
        
        ("10/19/25", "O/1368367/0000039", 10.00, 279, """Over 83.5 Receiving Yds - Justin Jefferson (N)
Anytime TD - Justin Jefferson (N)"""),
        
        ("10/20/25", "O/1368367/0000040", 10.00, 755, """Anytime TD - Sam LaPorta (N)
Anytime TD - Cade Otton (N)
3+ Receptions - Sam LaPorta (Y)"""),
        
        ("10/20/25", "O/1368367/0000041", 10.00, 794, """Anytime TD - Sam LaPorta (N)
Anytime TD - Cade Otton (N)"""),
        
        ("10/20/25", "O/1368367/0000042", 10.00, 390, """2+ Passing TDs - Baker Mayfield (Y)
4+ Receptions - Cade Otton (Y)
Moneyline - Lions (Y)"""),
    ]
    
    new_bets = []
    skipped_bets = []
    
    for date_str, bet_id, wager, odds, legs_text in bet_data:
        # Check if bet already exists
        if bet_exists(bet_id, historical_bets):
            skipped_bets.append(bet_id)
            print(f"Skipped (already exists): {bet_id}")
            continue
        
        bet_date = parse_bet_date(date_str)
        betting_site = parse_betting_site(bet_id)
        
        # Parse legs
        legs = parse_legs_string(legs_text, bet_date)
        
        # Determine bet type (SGP if all same game, otherwise parlay)
        unique_games = set()
        for leg in legs:
            if "away" in leg and "home" in leg:
                unique_games.add((leg["away"], leg["home"]))
        
        bet_type = "SGP" if len(unique_games) == 1 else "Parlay"
        
        # Create bet entry
        bet_entry = {
            "bet_id": bet_id,
            "betting_site": betting_site,
            "legs": legs,
            "name": f"{bet_date.strftime('%m/%d')} {bet_type}",
            "odds": f"+{odds}" if odds > 0 else str(odds),
            "wager": wager,
            "type": bet_type,
        }
        
        # Calculate returns (optional, can be filled later)
        if odds > 0:
            bet_entry["returns"] = f"{(wager * odds / 100):.2f}"
        
        new_bets.append(bet_entry)
        print(f"Added bet: {bet_id} - {len(legs)} legs")
    
    # Combine with existing and sort by date
    all_bets = historical_bets + new_bets
    all_bets = sort_historical_bets(all_bets)
    
    with open(historical_file, 'w') as f:
        json.dump(all_bets, f, indent=2)
    
    print(f"\nTotal bets now: {len(all_bets)}")
    print(f"Added {len(new_bets)} new bets")
    print(f"Skipped {len(skipped_bets)} duplicate bets")
    print(f"Sorted by game dates (newest first)")
    print(f"Saved to {historical_file}")

if __name__ == "__main__":
    main()
