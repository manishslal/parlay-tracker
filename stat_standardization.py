#!/usr/bin/env python3
"""
Stat Type Standardization Configuration

Task 9: Standardize stat types. Maps various formats and aliases to canonical stat names.
Supports multiple languages and common misspellings. Used for sport detection fallback.

Usage:
    from stat_standardization import standardize_stat_type
    canonical = standardize_stat_type('passing yds', sport='NFL')
"""

# NFL stat type mapping
NFL_STATS = {
    'passing_yards': ['passing_yards', 'passing yards', 'pass yards', 'pass_yards', 'passing yds', 'pass yds', 'alt_passing_yards', 'alt_passing_yds', 'passing_yards_alt', 'alt passing yards', 'alt pass yds'],
    'passing_touchdowns': ['passing_touchdowns', 'passing touchdowns', 'pass touchdowns', 'passing_td', 'passing td', 'pass td'],
    'interceptions_thrown': ['interceptions_thrown', 'interceptions thrown', 'interceptions', 'int_thrown'],
    'passing_completions': ['passing_completions', 'passing completions', 'completions', 'pass_completions'],
    'rushing_yards': ['rushing_yards', 'rushing yards', 'rush yards', 'rush_yards', 'rushing yds', 'rush yds', 'alt_rushing_yards', 'alt_rushing_yds', 'rushing_yards_alt', 'alt rushing yards', 'alt rush yds'],
    'rushing_touchdowns': ['rushing_touchdowns', 'rushing touchdowns', 'rush touchdowns', 'rushing_td', 'rushing td', 'rush td'],
    'rushing_attempts': ['rushing_attempts', 'rushing attempts', 'rush attempts', 'rushing_att', 'rush_att', 'carries'],
    'receiving_yards': ['receiving_yards', 'receiving yards', 'rec yards', 'rec_yards', 'receiving yds', 'rec yds', 'alt_receiving_yards', 'alt_receiving_yds', 'alt receiving yards', 'alt rec yds'],
    'receiving_touchdowns': ['receiving_touchdowns', 'receiving touchdowns', 'rec touchdowns', 'receiving_td', 'receiving td', 'rec td'],
    'receptions': ['receptions', 'reception', 'rec', 'catches', 'receptions_alt', 'alt_receptions', 'alt receptions'],
    'longest_reception': ['longest_reception', 'longest reception', 'longest rec'],
    'sacks': ['sacks', 'sack', 'sks', 'quarterback_sacks'],
    'tackles_assists': ['tackles_assists', 'tackles assists', 'tackles', 'tackle', 'total tackles'],
    'field_goals_made': ['field_goals_made', 'field goals made', 'fg made', 'field_goals', 'fgm'],
    'kicking_points': ['kicking_points', 'kicking points', 'points', 'kicker points'],
    'rushing_receiving_yards': ['rushing_receiving_yards', 'rushing receiving yards', 'rush receiving yards', 'alt_rushing_receiving_yards', 'alt rushing receiving yards'],
    'passing_rushing_yards': ['passing_rushing_yards', 'passing rushing yards', 'pass rushing yards'],
    'anytime_touchdown': ['anytime_touchdown', 'anytime td', 'anytime_td', 'anytime_td_scorer', 'any_time_touchdown_scorer', 'touchdown_scorer', 'td_scorer', 'any_td', 'anytime td scorer', 'touchdown scorer'],
    'team_total_points': ['team_total_points', 'team total points', 'team points', 'team_score'],
    'moneyline': ['moneyline', 'money line', 'ml', 'win'],
    'spread': ['spread', 'point spread', 'spread_total'],
}

# NBA stat type mapping
NBA_STATS = {
    'points': ['points', 'point', 'pts', 'scoring', 'score', 'player_points'],
    'three_pointers': ['three_pointers', 'three pointers', 'three_pointers_made', 'three pointers made', '3_pointers', '3 pointers', 'threes', '3pm'],
    'field_goals_made': ['field_goals_made', 'field goals made', 'fgm', 'field_goals'],
    'field_goal_percentage': ['field_goal_percentage', 'field goal percentage', 'fg%', 'fg_pct'],
    'rebounds': ['rebounds', 'rebound', 'reb', 'total rebounds', 'trb'],
    'offensive_rebounds': ['offensive_rebounds', 'offensive rebounds', 'off reb', 'orb'],
    'defensive_rebounds': ['defensive_rebounds', 'defensive rebounds', 'def reb', 'drb'],
    'assists': ['assists', 'assist', 'ast', 'total assists'],
    'turnovers': ['turnovers', 'turnover', 'to', 'total turnovers'],
    'steals': ['steals', 'steal', 'stl', 'total steals'],
    'blocks': ['blocks', 'block', 'blk', 'total blocks'],
    'plus_minus': ['plus_minus', '+/-', 'plus minus'],
    'points_rebounds_assists': ['points_rebounds_assists', 'points rebounds assists', 'pra', 'triple double'],
    'points_assists': ['points_assists', 'points assists', 'pts ast'],
    'rebounds_assists': ['rebounds_assists', 'rebounds assists', 'reb ast'],
    'moneyline': ['moneyline', 'money line', 'ml', 'win'],
    'spread': ['spread', 'point spread', 'spread_total'],
    'over_under': ['over_under', 'over under', 'o/u', 'total points'],
}

# MLB stat type mapping
MLB_STATS = {
    'home_runs': ['home_runs', 'home runs', 'home_run', 'home run', 'hrs', 'hr', 'homers'],
    'hits': ['hits', 'hit', 'h', 'total hits'],
    'runs_batted_in': ['runs_batted_in', 'runs batted in', 'rbi', 'rbis', 'runs_scored'],
    'runs': ['runs', 'run', 'r', 'total runs'],
    'batting_average': ['batting_average', 'batting average', 'avg', 'ba'],
    'strikeouts_batter': ['strikeouts_batter', 'strikeouts batter', 'k', 'strikeout', 'strikeouts'],
    'walks': ['walks', 'walk', 'bb', 'base on balls'],
    'doubles': ['doubles', 'double', '2b', 'two_base_hits'],
    'triples': ['triples', 'triple', '3b', 'three_base_hits'],
    'stolen_bases': ['stolen_bases', 'stolen bases', 'sb', 'steals'],
    'on_base_percentage': ['on_base_percentage', 'on base percentage', 'obp'],
    'strikeouts_pitcher': ['strikeouts_pitcher', 'strikeouts pitcher', 'pitcher strikeouts', 'strikeout'],
    'innings_pitched': ['innings_pitched', 'innings pitched', 'ip', 'innings'],
    'earned_runs': ['earned_runs', 'earned runs', 'er', 'runs_allowed'],
    'earned_run_average': ['earned_run_average', 'earned run average', 'era'],
    'hits_allowed': ['hits_allowed', 'hits allowed'],
    'walks_allowed': ['walks_allowed', 'walks allowed', 'walks'],
    'pitcher_wins': ['pitcher_wins', 'pitcher wins', 'wins', 'w'],
    'pitcher_saves': ['pitcher_saves', 'pitcher saves', 'saves', 'sv', 'save'],
    'moneyline': ['moneyline', 'money line', 'ml', 'win'],
    'run_line': ['run_line', 'run line', 'rl'],
    'total_runs': ['total_runs', 'total runs', 'total'],
}

# NHL stat type mapping
NHL_STATS = {
    'goals': ['goals', 'goal', 'g'],
    'assists': ['assists', 'assist', 'ast', 'a', 'total assists'],
    'points_hockey': ['points_hockey', 'points', 'pts', 'total points', 'goals_assists'],
    'shots_on_goal': ['shots_on_goal', 'shots on goal', 'sog', 'shots', 'shot'],
    'shooting_percentage': ['shooting_percentage', 'shooting percentage', 'sh%'],
    'saves': ['saves', 'save', 'sv'],
    'shutouts': ['shutouts', 'shutout', 'so'],
    'goals_against_average': ['goals_against_average', 'goals against average', 'gaa'],
    'save_percentage': ['save_percentage', 'save percentage', 'sv%'],
    'plus_minus': ['plus_minus', '+/-', 'plus minus'],
    'penalty_minutes': ['penalty_minutes', 'penalty minutes', 'pim', 'minutes'],
    'blocks': ['blocks', 'block', 'blk', 'shot blocks'],
    'hits': ['hits', 'hit', 'hc'],
    'moneyline': ['moneyline', 'money line', 'ml', 'win'],
    'puck_line': ['puck_line', 'puck line', 'pl'],
    'total_goals': ['total_goals', 'total goals', 'total'],
}

# Master stat type mapping by sport
STAT_TYPE_STANDARDIZATION = {
    'NFL': NFL_STATS,
    'NBA': NBA_STATS,
    'MLB': MLB_STATS,
    'NHL': NHL_STATS,
}


def standardize_stat_type(stat_type, sport=None):
    """
    Convert a stat type string to its canonical name.
    
    Args:
        stat_type (str): The stat type string to standardize
        sport (str, optional): The sport ('NFL', 'NBA', 'MLB', 'NHL')
        
    Returns:
        str: The canonical stat name, or original if no match found
    """
    if not stat_type:
        return stat_type
    
    stat_lower = stat_type.lower().strip()
    
    # If sport specified, search only that sport
    if sport and sport in STAT_TYPE_STANDARDIZATION:
        sport_map = STAT_TYPE_STANDARDIZATION[sport]
        for canonical, aliases in sport_map.items():
            if stat_lower in [a.lower() for a in aliases]:
                return canonical
    else:
        # Search all sports if no sport specified
        for sport_name, sport_map in STAT_TYPE_STANDARDIZATION.items():
            for canonical, aliases in sport_map.items():
                if stat_lower in [a.lower() for a in aliases]:
                    return canonical
    
    # Return original if no match found
    return stat_type


def get_stat_aliases(canonical_stat, sport):
    """Get all aliases for a canonical stat name in a specific sport."""
    if sport not in STAT_TYPE_STANDARDIZATION:
        return []
    
    sport_map = STAT_TYPE_STANDARDIZATION[sport]
    return sport_map.get(canonical_stat, [])


def get_all_stats_for_sport(sport):
    """Get all canonical stat names for a specific sport."""
    if sport not in STAT_TYPE_STANDARDIZATION:
        return []
    
    return list(STAT_TYPE_STANDARDIZATION[sport].keys())
