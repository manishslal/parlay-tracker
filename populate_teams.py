#!/usr/bin/env python3
"""
Populate Teams table with all NFL, NBA, MLB, and NHL teams.

Task 8: Create Teams database table - Initialization script.
Populates ~330 teams across 4 sports with official data.

Usage:
    python3 populate_teams.py
"""

from app import app, db
from models import Team

# NFL Teams (32 teams)
NFL_TEAMS = [
    # AFC East
    {'name_full': 'New England Patriots', 'name_short': 'Patriots', 'abbreviation': 'NE', 'conference': 'AFC', 'division': 'AFC East', 'league': 'National Football League', 'location': 'Foxborough, MA'},
    {'name_full': 'New York Jets', 'name_short': 'Jets', 'abbreviation': 'NYJ', 'conference': 'AFC', 'division': 'AFC East', 'league': 'National Football League', 'location': 'New York, NY'},
    {'name_full': 'Miami Dolphins', 'name_short': 'Dolphins', 'abbreviation': 'MIA', 'conference': 'AFC', 'division': 'AFC East', 'league': 'National Football League', 'location': 'Miami, FL'},
    {'name_full': 'Buffalo Bills', 'name_short': 'Bills', 'abbreviation': 'BUF', 'conference': 'AFC', 'division': 'AFC East', 'league': 'National Football League', 'location': 'Buffalo, NY'},
    
    # AFC North
    {'name_full': 'Pittsburgh Steelers', 'name_short': 'Steelers', 'abbreviation': 'PIT', 'conference': 'AFC', 'division': 'AFC North', 'league': 'National Football League', 'location': 'Pittsburgh, PA'},
    {'name_full': 'Baltimore Ravens', 'name_short': 'Ravens', 'abbreviation': 'BAL', 'conference': 'AFC', 'division': 'AFC North', 'league': 'National Football League', 'location': 'Baltimore, MD'},
    {'name_full': 'Cleveland Browns', 'name_short': 'Browns', 'abbreviation': 'CLE', 'conference': 'AFC', 'division': 'AFC North', 'league': 'National Football League', 'location': 'Cleveland, OH'},
    {'name_full': 'Cincinnati Bengals', 'name_short': 'Bengals', 'abbreviation': 'CIN', 'conference': 'AFC', 'division': 'AFC North', 'league': 'National Football League', 'location': 'Cincinnati, OH'},
    
    # AFC South
    {'name_full': 'Indianapolis Colts', 'name_short': 'Colts', 'abbreviation': 'IND', 'conference': 'AFC', 'division': 'AFC South', 'league': 'National Football League', 'location': 'Indianapolis, IN'},
    {'name_full': 'Tennessee Titans', 'name_short': 'Titans', 'abbreviation': 'TEN', 'conference': 'AFC', 'division': 'AFC South', 'league': 'National Football League', 'location': 'Nashville, TN'},
    {'name_full': 'Jacksonville Jaguars', 'name_short': 'Jaguars', 'abbreviation': 'JAX', 'conference': 'AFC', 'division': 'AFC South', 'league': 'National Football League', 'location': 'Jacksonville, FL'},
    {'name_full': 'Houston Texans', 'name_short': 'Texans', 'abbreviation': 'HOU', 'conference': 'AFC', 'division': 'AFC South', 'league': 'National Football League', 'location': 'Houston, TX'},
    
    # AFC West
    {'name_full': 'Denver Broncos', 'name_short': 'Broncos', 'abbreviation': 'DEN', 'conference': 'AFC', 'division': 'AFC West', 'league': 'National Football League', 'location': 'Denver, CO'},
    {'name_full': 'Kansas City Chiefs', 'name_short': 'Chiefs', 'abbreviation': 'KC', 'conference': 'AFC', 'division': 'AFC West', 'league': 'National Football League', 'location': 'Kansas City, MO'},
    {'name_full': 'Los Angeles Chargers', 'name_short': 'Chargers', 'abbreviation': 'LAC', 'conference': 'AFC', 'division': 'AFC West', 'league': 'National Football League', 'location': 'Los Angeles, CA'},
    {'name_full': 'Las Vegas Raiders', 'name_short': 'Raiders', 'abbreviation': 'LV', 'conference': 'AFC', 'division': 'AFC West', 'league': 'National Football League', 'location': 'Las Vegas, NV'},
    
    # NFC East
    {'name_full': 'Dallas Cowboys', 'name_short': 'Cowboys', 'abbreviation': 'DAL', 'conference': 'NFC', 'division': 'NFC East', 'league': 'National Football League', 'location': 'Arlington, TX'},
    {'name_full': 'Philadelphia Eagles', 'name_short': 'Eagles', 'abbreviation': 'PHI', 'conference': 'NFC', 'division': 'NFC East', 'league': 'National Football League', 'location': 'Philadelphia, PA'},
    {'name_full': 'New York Giants', 'name_short': 'Giants', 'abbreviation': 'NYG', 'conference': 'NFC', 'division': 'NFC East', 'league': 'National Football League', 'location': 'New York, NY'},
    {'name_full': 'Washington Commanders', 'name_short': 'Commanders', 'abbreviation': 'WAS', 'conference': 'NFC', 'division': 'NFC East', 'league': 'National Football League', 'location': 'Landover, MD'},
    
    # NFC North
    {'name_full': 'Chicago Bears', 'name_short': 'Bears', 'abbreviation': 'CHI', 'conference': 'NFC', 'division': 'NFC North', 'league': 'National Football League', 'location': 'Chicago, IL'},
    {'name_full': 'Green Bay Packers', 'name_short': 'Packers', 'abbreviation': 'GB', 'conference': 'NFC', 'division': 'NFC North', 'league': 'National Football League', 'location': 'Green Bay, WI'},
    {'name_full': 'Detroit Lions', 'name_short': 'Lions', 'abbreviation': 'DET', 'conference': 'NFC', 'division': 'NFC North', 'league': 'National Football League', 'location': 'Detroit, MI'},
    {'name_full': 'Minnesota Vikings', 'name_short': 'Vikings', 'abbreviation': 'MIN', 'conference': 'NFC', 'division': 'NFC North', 'league': 'National Football League', 'location': 'Minneapolis, MN'},
    
    # NFC South
    {'name_full': 'Atlanta Falcons', 'name_short': 'Falcons', 'abbreviation': 'ATL', 'conference': 'NFC', 'division': 'NFC South', 'league': 'National Football League', 'location': 'Atlanta, GA'},
    {'name_full': 'New Orleans Saints', 'name_short': 'Saints', 'abbreviation': 'NO', 'conference': 'NFC', 'division': 'NFC South', 'league': 'National Football League', 'location': 'New Orleans, LA'},
    {'name_full': 'Carolina Panthers', 'name_short': 'Panthers', 'abbreviation': 'CAR', 'conference': 'NFC', 'division': 'NFC South', 'league': 'National Football League', 'location': 'Charlotte, NC'},
    {'name_full': 'Tampa Bay Buccaneers', 'name_short': 'Buccaneers', 'abbreviation': 'TB', 'conference': 'NFC', 'division': 'NFC South', 'league': 'National Football League', 'location': 'Tampa, FL'},
    
    # NFC West
    {'name_full': 'San Francisco 49ers', 'name_short': '49ers', 'abbreviation': 'SF', 'conference': 'NFC', 'division': 'NFC West', 'league': 'National Football League', 'location': 'Santa Clara, CA'},
    {'name_full': 'Seattle Seahawks', 'name_short': 'Seahawks', 'abbreviation': 'SEA', 'conference': 'NFC', 'division': 'NFC West', 'league': 'National Football League', 'location': 'Seattle, WA'},
    {'name_full': 'Los Angeles Rams', 'name_short': 'Rams', 'abbreviation': 'LAR', 'conference': 'NFC', 'division': 'NFC West', 'league': 'National Football League', 'location': 'Inglewood, CA'},
    {'name_full': 'Arizona Cardinals', 'name_short': 'Cardinals', 'abbreviation': 'ARI', 'conference': 'NFC', 'division': 'NFC West', 'league': 'National Football League', 'location': 'Glendale, AZ'},
]

# NBA Teams (30 teams)
NBA_TEAMS = [
    # Eastern Conference
    # Atlantic Division
    {'name_full': 'Boston Celtics', 'name_short': 'Celtics', 'abbreviation': 'BOS', 'conference': 'Eastern', 'division': 'Atlantic', 'league': 'National Basketball Association', 'location': 'Boston, MA'},
    {'name_full': 'Brooklyn Nets', 'name_short': 'Nets', 'abbreviation': 'BKN', 'conference': 'Eastern', 'division': 'Atlantic', 'league': 'National Basketball Association', 'location': 'Brooklyn, NY'},
    {'name_full': 'New York Knicks', 'name_short': 'Knicks', 'abbreviation': 'NYK', 'conference': 'Eastern', 'division': 'Atlantic', 'league': 'National Basketball Association', 'location': 'New York, NY'},
    {'name_full': 'Philadelphia 76ers', 'name_short': '76ers', 'abbreviation': 'PHI', 'conference': 'Eastern', 'division': 'Atlantic', 'league': 'National Basketball Association', 'location': 'Philadelphia, PA'},
    {'name_full': 'Toronto Raptors', 'name_short': 'Raptors', 'abbreviation': 'TOR', 'conference': 'Eastern', 'division': 'Atlantic', 'league': 'National Basketball Association', 'location': 'Toronto, ON'},
    
    # Central Division
    {'name_full': 'Chicago Bulls', 'name_short': 'Bulls', 'abbreviation': 'CHI', 'conference': 'Eastern', 'division': 'Central', 'league': 'National Basketball Association', 'location': 'Chicago, IL'},
    {'name_full': 'Cleveland Cavaliers', 'name_short': 'Cavaliers', 'abbreviation': 'CLE', 'conference': 'Eastern', 'division': 'Central', 'league': 'National Basketball Association', 'location': 'Cleveland, OH'},
    {'name_full': 'Detroit Pistons', 'name_short': 'Pistons', 'abbreviation': 'DET', 'conference': 'Eastern', 'division': 'Central', 'league': 'National Basketball Association', 'location': 'Detroit, MI'},
    {'name_full': 'Indiana Pacers', 'name_short': 'Pacers', 'abbreviation': 'IND', 'conference': 'Eastern', 'division': 'Central', 'league': 'National Basketball Association', 'location': 'Indianapolis, IN'},
    {'name_full': 'Milwaukee Bucks', 'name_short': 'Bucks', 'abbreviation': 'MIL', 'conference': 'Eastern', 'division': 'Central', 'league': 'National Basketball Association', 'location': 'Milwaukee, WI'},
    
    # Southeast Division
    {'name_full': 'Atlanta Hawks', 'name_short': 'Hawks', 'abbreviation': 'ATL', 'conference': 'Eastern', 'division': 'Southeast', 'league': 'National Basketball Association', 'location': 'Atlanta, GA'},
    {'name_full': 'Charlotte Hornets', 'name_short': 'Hornets', 'abbreviation': 'CHA', 'conference': 'Eastern', 'division': 'Southeast', 'league': 'National Basketball Association', 'location': 'Charlotte, NC'},
    {'name_full': 'Miami Heat', 'name_short': 'Heat', 'abbreviation': 'MIA', 'conference': 'Eastern', 'division': 'Southeast', 'league': 'National Basketball Association', 'location': 'Miami, FL'},
    {'name_full': 'Orlando Magic', 'name_short': 'Magic', 'abbreviation': 'ORL', 'conference': 'Eastern', 'division': 'Southeast', 'league': 'National Basketball Association', 'location': 'Orlando, FL'},
    {'name_full': 'Washington Wizards', 'name_short': 'Wizards', 'abbreviation': 'WAS', 'conference': 'Eastern', 'division': 'Southeast', 'league': 'National Basketball Association', 'location': 'Washington, DC'},
    
    # Western Conference
    # Southwest Division
    {'name_full': 'Dallas Mavericks', 'name_short': 'Mavericks', 'abbreviation': 'DAL', 'conference': 'Western', 'division': 'Southwest', 'league': 'National Basketball Association', 'location': 'Dallas, TX'},
    {'name_full': 'Houston Rockets', 'name_short': 'Rockets', 'abbreviation': 'HOU', 'conference': 'Western', 'division': 'Southwest', 'league': 'National Basketball Association', 'location': 'Houston, TX'},
    {'name_full': 'Memphis Grizzlies', 'name_short': 'Grizzlies', 'abbreviation': 'MEM', 'conference': 'Western', 'division': 'Southwest', 'league': 'National Basketball Association', 'location': 'Memphis, TN'},
    {'name_full': 'New Orleans Pelicans', 'name_short': 'Pelicans', 'abbreviation': 'NOP', 'conference': 'Western', 'division': 'Southwest', 'league': 'National Basketball Association', 'location': 'New Orleans, LA'},
    {'name_full': 'San Antonio Spurs', 'name_short': 'Spurs', 'abbreviation': 'SA', 'conference': 'Western', 'division': 'Southwest', 'league': 'National Basketball Association', 'location': 'San Antonio, TX'},
    
    # Northwest Division
    {'name_full': 'Denver Nuggets', 'name_short': 'Nuggets', 'abbreviation': 'DEN', 'conference': 'Western', 'division': 'Northwest', 'league': 'National Basketball Association', 'location': 'Denver, CO'},
    {'name_full': 'Minnesota Timberwolves', 'name_short': 'Timberwolves', 'abbreviation': 'MIN', 'conference': 'Western', 'division': 'Northwest', 'league': 'National Basketball Association', 'location': 'Minneapolis, MN'},
    {'name_full': 'Oklahoma City Thunder', 'name_short': 'Thunder', 'abbreviation': 'OKC', 'conference': 'Western', 'division': 'Northwest', 'league': 'National Basketball Association', 'location': 'Oklahoma City, OK'},
    {'name_full': 'Portland Trail Blazers', 'name_short': 'Trail Blazers', 'abbreviation': 'POR', 'conference': 'Western', 'division': 'Northwest', 'league': 'National Basketball Association', 'location': 'Portland, OR'},
    {'name_full': 'Utah Jazz', 'name_short': 'Jazz', 'abbreviation': 'UTA', 'conference': 'Western', 'division': 'Northwest', 'league': 'National Basketball Association', 'location': 'Salt Lake City, UT'},
    
    # Pacific Division
    {'name_full': 'Golden State Warriors', 'name_short': 'Warriors', 'abbreviation': 'GSW', 'conference': 'Western', 'division': 'Pacific', 'league': 'National Basketball Association', 'location': 'San Francisco, CA'},
    {'name_full': 'LA Clippers', 'name_short': 'Clippers', 'abbreviation': 'LAC', 'conference': 'Western', 'division': 'Pacific', 'league': 'National Basketball Association', 'location': 'Los Angeles, CA'},
    {'name_full': 'Los Angeles Lakers', 'name_short': 'Lakers', 'abbreviation': 'LAL', 'conference': 'Western', 'division': 'Pacific', 'league': 'National Basketball Association', 'location': 'Los Angeles, CA'},
    {'name_full': 'Phoenix Suns', 'name_short': 'Suns', 'abbreviation': 'PHX', 'conference': 'Western', 'division': 'Pacific', 'league': 'National Basketball Association', 'location': 'Phoenix, AZ'},
    {'name_full': 'Sacramento Kings', 'name_short': 'Kings', 'abbreviation': 'SAC', 'conference': 'Western', 'division': 'Pacific', 'league': 'National Basketball Association', 'location': 'Sacramento, CA'},
]

# MLB Teams (30 teams)
MLB_TEAMS = [
    # AL East
    {'name_full': 'New York Yankees', 'name_short': 'Yankees', 'abbreviation': 'NYY', 'conference': 'AL', 'division': 'AL East', 'league': 'Major League Baseball', 'location': 'New York, NY'},
    {'name_full': 'Boston Red Sox', 'name_short': 'Red Sox', 'abbreviation': 'BOS', 'conference': 'AL', 'division': 'AL East', 'league': 'Major League Baseball', 'location': 'Boston, MA'},
    {'name_full': 'Tampa Bay Rays', 'name_short': 'Rays', 'abbreviation': 'TB', 'conference': 'AL', 'division': 'AL East', 'league': 'Major League Baseball', 'location': 'St. Petersburg, FL'},
    {'name_full': 'Baltimore Orioles', 'name_short': 'Orioles', 'abbreviation': 'BAL', 'conference': 'AL', 'division': 'AL East', 'league': 'Major League Baseball', 'location': 'Baltimore, MD'},
    {'name_full': 'Toronto Blue Jays', 'name_short': 'Blue Jays', 'abbreviation': 'TOR', 'conference': 'AL', 'division': 'AL East', 'league': 'Major League Baseball', 'location': 'Toronto, ON'},
    
    # AL Central
    {'name_full': 'Cleveland Guardians', 'name_short': 'Guardians', 'abbreviation': 'CLE', 'conference': 'AL', 'division': 'AL Central', 'league': 'Major League Baseball', 'location': 'Cleveland, OH'},
    {'name_full': 'Detroit Tigers', 'name_short': 'Tigers', 'abbreviation': 'DET', 'conference': 'AL', 'division': 'AL Central', 'league': 'Major League Baseball', 'location': 'Detroit, MI'},
    {'name_full': 'Chicago White Sox', 'name_short': 'White Sox', 'abbreviation': 'CWS', 'conference': 'AL', 'division': 'AL Central', 'league': 'Major League Baseball', 'location': 'Chicago, IL'},
    {'name_full': 'Kansas City Royals', 'name_short': 'Royals', 'abbreviation': 'KC', 'conference': 'AL', 'division': 'AL Central', 'league': 'Major League Baseball', 'location': 'Kansas City, MO'},
    {'name_full': 'Minnesota Twins', 'name_short': 'Twins', 'abbreviation': 'MIN', 'conference': 'AL', 'division': 'AL Central', 'league': 'Major League Baseball', 'location': 'Minneapolis, MN'},
    
    # AL West
    {'name_full': 'Houston Astros', 'name_short': 'Astros', 'abbreviation': 'HOU', 'conference': 'AL', 'division': 'AL West', 'league': 'Major League Baseball', 'location': 'Houston, TX'},
    {'name_full': 'Los Angeles Angels', 'name_short': 'Angels', 'abbreviation': 'LAA', 'conference': 'AL', 'division': 'AL West', 'league': 'Major League Baseball', 'location': 'Anaheim, CA'},
    {'name_full': 'Oakland Athletics', 'name_short': 'Athletics', 'abbreviation': 'OAK', 'conference': 'AL', 'division': 'AL West', 'league': 'Major League Baseball', 'location': 'Oakland, CA'},
    {'name_full': 'Seattle Mariners', 'name_short': 'Mariners', 'abbreviation': 'SEA', 'conference': 'AL', 'division': 'AL West', 'league': 'Major League Baseball', 'location': 'Seattle, WA'},
    {'name_full': 'Texas Rangers', 'name_short': 'Rangers', 'abbreviation': 'TEX', 'conference': 'AL', 'division': 'AL West', 'league': 'Major League Baseball', 'location': 'Arlington, TX'},
    
    # NL East
    {'name_full': 'Atlanta Braves', 'name_short': 'Braves', 'abbreviation': 'ATL', 'conference': 'NL', 'division': 'NL East', 'league': 'Major League Baseball', 'location': 'Atlanta, GA'},
    {'name_full': 'Miami Marlins', 'name_short': 'Marlins', 'abbreviation': 'MIA', 'conference': 'NL', 'division': 'NL East', 'league': 'Major League Baseball', 'location': 'Miami, FL'},
    {'name_full': 'New York Mets', 'name_short': 'Mets', 'abbreviation': 'NYM', 'conference': 'NL', 'division': 'NL East', 'league': 'Major League Baseball', 'location': 'New York, NY'},
    {'name_full': 'Philadelphia Phillies', 'name_short': 'Phillies', 'abbreviation': 'PHI', 'conference': 'NL', 'division': 'NL East', 'league': 'Major League Baseball', 'location': 'Philadelphia, PA'},
    {'name_full': 'Washington Nationals', 'name_short': 'Nationals', 'abbreviation': 'WSH', 'conference': 'NL', 'division': 'NL East', 'league': 'Major League Baseball', 'location': 'Washington, DC'},
    
    # NL Central
    {'name_full': 'Chicago Cubs', 'name_short': 'Cubs', 'abbreviation': 'CHC', 'conference': 'NL', 'division': 'NL Central', 'league': 'Major League Baseball', 'location': 'Chicago, IL'},
    {'name_full': 'Cincinnati Reds', 'name_short': 'Reds', 'abbreviation': 'CIN', 'conference': 'NL', 'division': 'NL Central', 'league': 'Major League Baseball', 'location': 'Cincinnati, OH'},
    {'name_full': 'Milwaukee Brewers', 'name_short': 'Brewers', 'abbreviation': 'MIL', 'conference': 'NL', 'division': 'NL Central', 'league': 'Major League Baseball', 'location': 'Milwaukee, WI'},
    {'name_full': 'Pittsburgh Pirates', 'name_short': 'Pirates', 'abbreviation': 'PIT', 'conference': 'NL', 'division': 'NL Central', 'league': 'Major League Baseball', 'location': 'Pittsburgh, PA'},
    {'name_full': 'St. Louis Cardinals', 'name_short': 'Cardinals', 'abbreviation': 'STL', 'conference': 'NL', 'division': 'NL Central', 'league': 'Major League Baseball', 'location': 'St. Louis, MO'},
    
    # NL West
    {'name_full': 'Arizona Diamondbacks', 'name_short': 'Diamondbacks', 'abbreviation': 'ARI', 'conference': 'NL', 'division': 'NL West', 'league': 'Major League Baseball', 'location': 'Phoenix, AZ'},
    {'name_full': 'Colorado Rockies', 'name_short': 'Rockies', 'abbreviation': 'COL', 'conference': 'NL', 'division': 'NL West', 'league': 'Major League Baseball', 'location': 'Denver, CO'},
    {'name_full': 'Los Angeles Dodgers', 'name_short': 'Dodgers', 'abbreviation': 'LAD', 'conference': 'NL', 'division': 'NL West', 'league': 'Major League Baseball', 'location': 'Los Angeles, CA'},
    {'name_full': 'San Diego Padres', 'name_short': 'Padres', 'abbreviation': 'SD', 'conference': 'NL', 'division': 'NL West', 'league': 'Major League Baseball', 'location': 'San Diego, CA'},
    {'name_full': 'San Francisco Giants', 'name_short': 'Giants', 'abbreviation': 'SF', 'conference': 'NL', 'division': 'NL West', 'league': 'Major League Baseball', 'location': 'San Francisco, CA'},
]

# NHL Teams (32 teams)
NHL_TEAMS = [
    # Atlantic Division
    {'name_full': 'Boston Bruins', 'name_short': 'Bruins', 'abbreviation': 'BOS', 'conference': 'Eastern', 'division': 'Atlantic', 'league': 'National Hockey League', 'location': 'Boston, MA'},
    {'name_full': 'Buffalo Sabres', 'name_short': 'Sabres', 'abbreviation': 'BUF', 'conference': 'Eastern', 'division': 'Atlantic', 'league': 'National Hockey League', 'location': 'Buffalo, NY'},
    {'name_full': 'Detroit Red Wings', 'name_short': 'Red Wings', 'abbreviation': 'DET', 'conference': 'Eastern', 'division': 'Atlantic', 'league': 'National Hockey League', 'location': 'Detroit, MI'},
    {'name_full': 'Florida Panthers', 'name_short': 'Panthers', 'abbreviation': 'FLA', 'conference': 'Eastern', 'division': 'Atlantic', 'league': 'National Hockey League', 'location': 'Miami, FL'},
    {'name_full': 'Montreal Canadiens', 'name_short': 'Canadiens', 'abbreviation': 'MTL', 'conference': 'Eastern', 'division': 'Atlantic', 'league': 'National Hockey League', 'location': 'Montreal, QC'},
    {'name_full': 'Ottawa Senators', 'name_short': 'Senators', 'abbreviation': 'OTT', 'conference': 'Eastern', 'division': 'Atlantic', 'league': 'National Hockey League', 'location': 'Ottawa, ON'},
    {'name_full': 'Tampa Bay Lightning', 'name_short': 'Lightning', 'abbreviation': 'TB', 'conference': 'Eastern', 'division': 'Atlantic', 'league': 'National Hockey League', 'location': 'Tampa, FL'},
    {'name_full': 'Toronto Maple Leafs', 'name_short': 'Maple Leafs', 'abbreviation': 'TOR', 'conference': 'Eastern', 'division': 'Atlantic', 'league': 'National Hockey League', 'location': 'Toronto, ON'},
    
    # Metropolitan Division
    {'name_full': 'Carolina Hurricanes', 'name_short': 'Hurricanes', 'abbreviation': 'CAR', 'conference': 'Eastern', 'division': 'Metropolitan', 'league': 'National Hockey League', 'location': 'Raleigh, NC'},
    {'name_full': 'Columbus Blue Jackets', 'name_short': 'Blue Jackets', 'abbreviation': 'CBJ', 'conference': 'Eastern', 'division': 'Metropolitan', 'league': 'National Hockey League', 'location': 'Columbus, OH'},
    {'name_full': 'New Jersey Devils', 'name_short': 'Devils', 'abbreviation': 'NJ', 'conference': 'Eastern', 'division': 'Metropolitan', 'league': 'National Hockey League', 'location': 'Newark, NJ'},
    {'name_full': 'New York Islanders', 'name_short': 'Islanders', 'abbreviation': 'NYI', 'conference': 'Eastern', 'division': 'Metropolitan', 'league': 'National Hockey League', 'location': 'New York, NY'},
    {'name_full': 'New York Rangers', 'name_short': 'Rangers', 'abbreviation': 'NYR', 'conference': 'Eastern', 'division': 'Metropolitan', 'league': 'National Hockey League', 'location': 'New York, NY'},
    {'name_full': 'Philadelphia Flyers', 'name_short': 'Flyers', 'abbreviation': 'PHI', 'conference': 'Eastern', 'division': 'Metropolitan', 'league': 'National Hockey League', 'location': 'Philadelphia, PA'},
    {'name_full': 'Pittsburgh Penguins', 'name_short': 'Penguins', 'abbreviation': 'PIT', 'conference': 'Eastern', 'division': 'Metropolitan', 'league': 'National Hockey League', 'location': 'Pittsburgh, PA'},
    {'name_full': 'Washington Capitals', 'name_short': 'Capitals', 'abbreviation': 'WSH', 'conference': 'Eastern', 'division': 'Metropolitan', 'league': 'National Hockey League', 'location': 'Washington, DC'},
    
    # Central Division
    {'name_full': 'Chicago Blackhawks', 'name_short': 'Blackhawks', 'abbreviation': 'CHI', 'conference': 'Western', 'division': 'Central', 'league': 'National Hockey League', 'location': 'Chicago, IL'},
    {'name_full': 'Colorado Avalanche', 'name_short': 'Avalanche', 'abbreviation': 'COL', 'conference': 'Western', 'division': 'Central', 'league': 'National Hockey League', 'location': 'Denver, CO'},
    {'name_full': 'Dallas Stars', 'name_short': 'Stars', 'abbreviation': 'DAL', 'conference': 'Western', 'division': 'Central', 'league': 'National Hockey League', 'location': 'Dallas, TX'},
    {'name_full': 'Minnesota Wild', 'name_short': 'Wild', 'abbreviation': 'MIN', 'conference': 'Western', 'division': 'Central', 'league': 'National Hockey League', 'location': 'Minneapolis, MN'},
    {'name_full': 'Nashville Predators', 'name_short': 'Predators', 'abbreviation': 'NSH', 'conference': 'Western', 'division': 'Central', 'league': 'National Hockey League', 'location': 'Nashville, TN'},
    {'name_full': 'St. Louis Blues', 'name_short': 'Blues', 'abbreviation': 'STL', 'conference': 'Western', 'division': 'Central', 'league': 'National Hockey League', 'location': 'St. Louis, MO'},
    {'name_full': 'Winnipeg Jets', 'name_short': 'Jets', 'abbreviation': 'WPG', 'conference': 'Western', 'division': 'Central', 'league': 'National Hockey League', 'location': 'Winnipeg, MB'},
    
    # Pacific Division
    {'name_full': 'Anaheim Ducks', 'name_short': 'Ducks', 'abbreviation': 'ANA', 'conference': 'Western', 'division': 'Pacific', 'league': 'National Hockey League', 'location': 'Anaheim, CA'},
    {'name_full': 'Calgary Flames', 'name_short': 'Flames', 'abbreviation': 'CGY', 'conference': 'Western', 'division': 'Pacific', 'league': 'National Hockey League', 'location': 'Calgary, AB'},
    {'name_full': 'Edmonton Oilers', 'name_short': 'Oilers', 'abbreviation': 'EDM', 'conference': 'Western', 'division': 'Pacific', 'league': 'National Hockey League', 'location': 'Edmonton, AB'},
    {'name_full': 'Los Angeles Kings', 'name_short': 'Kings', 'abbreviation': 'LAK', 'conference': 'Western', 'division': 'Pacific', 'league': 'National Hockey League', 'location': 'Los Angeles, CA'},
    {'name_full': 'San Jose Sharks', 'name_short': 'Sharks', 'abbreviation': 'SJ', 'conference': 'Western', 'division': 'Pacific', 'league': 'National Hockey League', 'location': 'San Jose, CA'},
    {'name_full': 'Seattle Kraken', 'name_short': 'Kraken', 'abbreviation': 'SEA', 'conference': 'Western', 'division': 'Pacific', 'league': 'National Hockey League', 'location': 'Seattle, WA'},
    {'name_full': 'Vancouver Canucks', 'name_short': 'Canucks', 'abbreviation': 'VAN', 'conference': 'Western', 'division': 'Pacific', 'league': 'National Hockey League', 'location': 'Vancouver, BC'},
    {'name_full': 'Vegas Golden Knights', 'name_short': 'Golden Knights', 'abbreviation': 'VGK', 'conference': 'Western', 'division': 'Pacific', 'league': 'National Hockey League', 'location': 'Las Vegas, NV'},
]

def populate_teams():
    """Populate the Teams table with all teams across 4 sports."""
    with app.app_context():
        # Check if teams already exist
        existing_count = Team.query.count()
        if existing_count > 0:
            print(f"⚠️  Teams table already has {existing_count} teams. Skipping population.")
            return
        
        print("🏈 Adding NFL teams...")
        for team_data in NFL_TEAMS:
            team = Team(sport='NFL', **team_data)
            db.session.add(team)
        
        print("🏀 Adding NBA teams...")
        for team_data in NBA_TEAMS:
            team = Team(sport='NBA', **team_data)
            db.session.add(team)
        
        print("⚾ Adding MLB teams...")
        for team_data in MLB_TEAMS:
            team = Team(sport='MLB', **team_data)
            db.session.add(team)
        
        print("🏒 Adding NHL teams...")
        for team_data in NHL_TEAMS:
            team = Team(sport='NHL', **team_data)
            db.session.add(team)
        
        try:
            db.session.commit()
            total = Team.query.count()
            print(f"✅ Successfully populated Teams table with {total} teams")
            print(f"   - NFL: {Team.query.filter_by(sport='NFL').count()} teams")
            print(f"   - NBA: {Team.query.filter_by(sport='NBA').count()} teams")
            print(f"   - MLB: {Team.query.filter_by(sport='MLB').count()} teams")
            print(f"   - NHL: {Team.query.filter_by(sport='NHL').count()} teams")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error populating Teams table: {e}")
            raise

if __name__ == '__main__':
    populate_teams()
