"""
Team Name Utilities

Utility functions for team name standardization and matching.
"""

def find_team_name_short(team_name, name_to_short, abbr_to_short):
    """Find the team_name_short for a given team name using various matching strategies."""
    if not team_name or not team_name.strip():
        return None

    team_name_lower = team_name.lower().strip()

    # Direct match in name_to_short
    if team_name_lower in name_to_short:
        return name_to_short[team_name_lower]

    # Check if it's an abbreviation
    if team_name_lower in abbr_to_short:
        return abbr_to_short[team_name_lower]

    # Try partial matching for common abbreviations
    # Check if it's a common abbreviation pattern
    if len(team_name) <= 3 and team_name.isupper():
        if team_name_lower in abbr_to_short:
            return abbr_to_short[team_name_lower]

    # Try to match by extracting last word (for names like "Kansas City Chiefs" -> "Chiefs")
    if ' ' in team_name:
        last_word = team_name.split()[-1].lower()
        if last_word in name_to_short:
            return name_to_short[last_word]

    # Try to match by extracting first word (for names like "New England Patriots" -> "Patriots" might be in abbr)
    if ' ' in team_name:
        first_word = team_name.split()[0].lower()
        if first_word in abbr_to_short:
            return abbr_to_short[first_word]

    # If no match found, return None (don't change)
    return None