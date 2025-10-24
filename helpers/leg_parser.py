"""
Leg parsing helpers - parse bet leg text into structured data
"""

import re
from datetime import datetime
from typing import Dict, List, Tuple
from .nfl_data import NFL_TEAMS, PLAYER_TEAMS_2025
from .espn_api import find_game_for_team

def parse_stat_type(leg_text: str) -> Tuple[str, str, float, bool]:
    """
    Parse a leg text to extract stat type, player/team, and target
    Returns: (stat, player_or_team, target, is_player_prop)
    """
    leg_text = leg_text.strip()
    
    # Moneyline
    if leg_text.startswith("ML - ") or leg_text.startswith("Moneyline - "):
        team = leg_text.split(" - ", 1)[1].strip()
        # Expand short team names
        for short, full in NFL_TEAMS.items():
            if short in team:
                team = full
                break
        return ("moneyline", team, 1, False)
    
    # Spread
    if "Spread" in leg_text:
        match = re.search(r'Spread ([+-]?[\d.]+)', leg_text)
        if match:
            spread = float(match.group(1))
            team_match = re.search(r'- (.+)', leg_text)
            team = team_match.group(1).strip() if team_match else "Unknown"
            for short, full in NFL_TEAMS.items():
                if short in team:
                    team = full
                    break
            return ("spread", team, spread, False)
    
    # Anytime TD
    if "Anytime TD" in leg_text or "TD Scorer" in leg_text:
        player_match = re.search(r'(?:Anytime TD.*?-|TD Scorer.*?-)\s*(.+)', leg_text)
        player = player_match.group(1).strip() if player_match else "Unknown"
        return ("anytime_touchdown", player, 1, True)
    
    # First TD
    if "First TD" in leg_text:
        player_match = re.search(r'First TD.*?-\s*(.+)', leg_text)
        player = player_match.group(1).strip() if player_match else "Unknown"
        return ("first_touchdown", player, 1, True)
    
    # Passing yards
    if "Pass Yds" in leg_text or "Passing Yds" in leg_text or "Passing Yards" in leg_text:
        yards_match = re.search(r'(\d+)\+?\s*(?:Alt\s*)?Pass', leg_text)
        player_match = re.search(r'-\s*(.+?)(?:\s*\(|$)', leg_text)
        yards = float(yards_match.group(1)) if yards_match else 0
        player = player_match.group(1).strip() if player_match else "Unknown"
        return ("passing_yards", player, yards, True)
    
    # Passing TDs
    if "Pass TD" in leg_text or "Passing TD" in leg_text:
        tds_match = re.search(r'(\d+)\+?\s*Pass', leg_text)
        player_match = re.search(r'-\s*(.+?)(?:\s*\(|$)', leg_text)
        tds = float(tds_match.group(1)) if tds_match else 0
        player = player_match.group(1).strip() if player_match else "Unknown"
        return ("passing_touchdowns", player, tds, True)
    
    # Rushing yards
    if "Rush Yds" in leg_text or "Rushing Yds" in leg_text or "Rushing Yards" in leg_text:
        yards_match = re.search(r'(\d+)\+?\s*Rush', leg_text)
        player_match = re.search(r'-\s*(.+?)(?:\s*\(|$)', leg_text)
        yards = float(yards_match.group(1)) if yards_match else 0
        player = player_match.group(1).strip() if player_match else "Unknown"
        return ("rushing_yards", player, yards, True)
    
    # Receiving yards
    if "Rec Yds" in leg_text or "Receiving Yds" in leg_text or "Receiving Yards" in leg_text:
        yards_match = re.search(r'(\d+)\+?\s*(?:Alt\s*)?Rec', leg_text)
        player_match = re.search(r'-\s*(.+?)(?:\s*\(|$)', leg_text)
        yards = float(yards_match.group(1)) if yards_match else 0
        player = player_match.group(1).strip() if player_match else "Unknown"
        return ("receiving_yards", player, yards, True)
    
    # Receptions
    if "Receptions" in leg_text or leg_text.endswith("+ Rec"):
        recs_match = re.search(r'(\d+)\+?\s*Rec', leg_text)
        player_match = re.search(r'-\s*(.+?)(?:\s*\(|$)', leg_text)
        recs = float(recs_match.group(1)) if recs_match else 0
        player = player_match.group(1).strip() if player_match else "Unknown"
        return ("receptions", player, recs, True)
    
    # Rush + Rec yards combined
    if "Rush & Rec" in leg_text or "Rushing & Receiving" in leg_text:
        yards_match = re.search(r'(\d+)\+?', leg_text)
        player_match = re.search(r'-\s*(.+?)(?:\s*\(|$)', leg_text)
        yards = float(yards_match.group(1)) if yards_match else 0
        player = player_match.group(1).strip() if player_match else "Unknown"
        return ("rushing_receiving_yards", player, yards, True)
    
    # Over/Under props
    if "Over" in leg_text:
        value_match = re.search(r'Over ([\d.]+)', leg_text)
        player_match = re.search(r'-\s*(.+?)(?:\s*\(|$)', leg_text)
        value = float(value_match.group(1)) if value_match else 0
        player = player_match.group(1).strip() if player_match else "Unknown"
        
        if "Rec Yds" in leg_text or "Receiving" in leg_text:
            return ("receiving_yards", player, value, True)
        elif "Rush Yds" in leg_text or "Rushing" in leg_text:
            return ("rushing_yards", player, value, True)
        elif "Pass TD" in leg_text:
            return ("passing_touchdowns", player, value, True)
        elif "Longest Rec" in leg_text:
            return ("longest_reception", player, value, True)
    
    # Under props
    if "Under" in leg_text:
        value_match = re.search(r'Under ([\d.]+)', leg_text)
        player_match = re.search(r'-\s*(.+?)(?:\s*\(|$)', leg_text)
        value = float(value_match.group(1)) if value_match else 0
        player = player_match.group(1).strip() if player_match else "Unknown"
        
        if "Pass Yds" in leg_text:
            return ("passing_yards_under", player, value, True)
    
    # Total points
    if "Total Points" in leg_text:
        value_match = re.search(r'([\d.]+)', leg_text)
        matchup_match = re.search(r'-\s*(.+?)(?:\s*\(|$)', leg_text)
        value = float(value_match.group(1)) if value_match else 0
        matchup = matchup_match.group(1).strip() if matchup_match else "Unknown"
        return ("total_points", matchup, value, False)
    
    print(f"Warning: Could not parse leg: '{leg_text}'")
    return ("unknown", "Unknown", 0, True)

def find_game_for_player(player: str, bet_date: datetime) -> Tuple[str, str, str]:
    """
    Find the game matchup for a player based on bet date using ESPN API
    Returns: (away_team, home_team, game_date)
    """
    team = PLAYER_TEAMS_2025.get(player)
    if not team:
        print(f"Warning: Unknown player '{player}', using placeholder")
        return ("Unknown Team", "Unknown Team", bet_date.strftime("%Y-%m-%d"))
    
    return find_game_for_team(team, bet_date)

def parse_legs_string(legs_str: str, bet_date: datetime) -> List[Dict]:
    """Parse the legs string and return list of leg dictionaries"""
    legs = []
    
    # Split by newlines and clean up
    leg_lines = [l.strip() for l in legs_str.split('\n') if l.strip()]
    
    for leg_line in leg_lines:
        # Check for (Y) or (N) at the end for hit/miss status
        current = 0
        if leg_line.endswith('(Y)'):
            current = 1
            leg_line = leg_line[:-3].strip()
        elif leg_line.endswith('(N)'):
            current = 0
            leg_line = leg_line[:-3].strip()
        elif leg_line.endswith('(NULL)'):
            current = 0
            leg_line = leg_line[:-6].strip()
        
        # Parse the stat type
        stat, player_or_team, target, is_player_prop = parse_stat_type(leg_line)
        
        # Find the game matchup
        if is_player_prop:
            away, home, game_date = find_game_for_player(player_or_team, bet_date)
            leg_dict = {
                "target": target,
                "stat": stat,
                "current": current,
                "player": player_or_team,
                "away": away,
                "home": home,
                "game_date": game_date
            }
        else:
            # Team prop (moneyline, spread, total points)
            if stat == "total_points":
                # For total points, matchup is stored as "Team1 vs Team2"
                leg_dict = {
                    "target": target,
                    "stat": stat,
                    "current": current,
                    "team": player_or_team,
                    "away": "Unknown Team",
                    "home": "Unknown Team",
                    "game_date": bet_date.strftime("%Y-%m-%d")
                }
            else:
                away, home, game_date = find_game_for_team(player_or_team, bet_date)
                leg_dict = {
                    "target": target,
                    "stat": stat,
                    "current": current,
                    "team": player_or_team,
                    "away": away,
                    "home": home,
                    "game_date": game_date
                }
        
        legs.append(leg_dict)
    
    return legs
