from app import app
from models import db, Team

def seed_teams():
    """Populate the database with standard NFL and NBA teams."""
    
    # Abbreviation Mappings
    nfl_abbr = {
        "Arizona Cardinals": "ARI", "Atlanta Falcons": "ATL", "Baltimore Ravens": "BAL", "Buffalo Bills": "BUF",
        "Carolina Panthers": "CAR", "Chicago Bears": "CHI", "Cincinnati Bengals": "CIN", "Cleveland Browns": "CLE",
        "Dallas Cowboys": "DAL", "Denver Broncos": "DEN", "Detroit Lions": "DET", "Green Bay Packers": "GB",
        "Houston Texans": "HOU", "Indianapolis Colts": "IND", "Jacksonville Jaguars": "JAX", "Kansas City Chiefs": "KC",
        "Las Vegas Raiders": "LV", "Los Angeles Chargers": "LAC", "Los Angeles Rams": "LAR", "Miami Dolphins": "MIA",
        "Minnesota Vikings": "MIN", "New England Patriots": "NE", "New Orleans Saints": "NO", "New York Giants": "NYG",
        "New York Jets": "NYJ", "Philadelphia Eagles": "PHI", "Pittsburgh Steelers": "PIT", "San Francisco 49ers": "SF",
        "Seattle Seahawks": "SEA", "Tampa Bay Buccaneers": "TB", "Tennessee Titans": "TEN", "Washington Commanders": "WAS"
    }

    nba_abbr = {
        "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Brooklyn Nets": "BKN", "Charlotte Hornets": "CHA",
        "Chicago Bulls": "CHI", "Cleveland Cavaliers": "CLE", "Dallas Mavericks": "DAL", "Denver Nuggets": "DEN",
        "Detroit Pistons": "DET", "Golden State Warriors": "GS", "Houston Rockets": "HOU", "Indiana Pacers": "IND",
        "Los Angeles Clippers": "LAC", "Los Angeles Lakers": "LAL", "Memphis Grizzlies": "MEM", "Miami Heat": "MIA",
        "Milwaukee Bucks": "MIL", "Minnesota Timberwolves": "MIN", "New Orleans Pelicans": "NO", "New York Knicks": "NYK",
        "Oklahoma City Thunder": "OKC", "Orlando Magic": "ORL", "Philadelphia 76ers": "PHI", "Phoenix Suns": "PHX",
        "Portland Trail Blazers": "POR", "Sacramento Kings": "SAC", "San Antonio Spurs": "SA", "Toronto Raptors": "TOR",
        "Utah Jazz": "UTA", "Washington Wizards": "WAS"
    }

    # Data from search result (simplified structure)
    teams_data = [
        # NFL
        {"name": "Arizona Cardinals", "color": "#97233F", "alt": "#000000", "logo": "https://upload.wikimedia.org/wikipedia/en/b/b9/Arizona_Cardinals_logo.svg", "sport": "NFL"},
        {"name": "Atlanta Falcons", "color": "#A71930", "alt": "#000000", "logo": "https://upload.wikimedia.org/wikipedia/en/c/c5/Atlanta_Falcons_logo.svg", "sport": "NFL"},
        {"name": "Baltimore Ravens", "color": "#241773", "alt": "#000000", "logo": "https://upload.wikimedia.org/wikipedia/en/1/16/Baltimore_Ravens_logo.svg", "sport": "NFL"},
        {"name": "Buffalo Bills", "color": "#00338D", "alt": "#C60C30", "logo": "https://upload.wikimedia.org/wikipedia/en/7/77/Buffalo_Bills_logo.svg", "sport": "NFL"},
        {"name": "Carolina Panthers", "color": "#0085CA", "alt": "#000000", "logo": "https://upload.wikimedia.org/wikipedia/en/c/cd/Carolina_Panthers_logo.svg", "sport": "NFL"},
        {"name": "Chicago Bears", "color": "#0B162A", "alt": "#CB6015", "logo": "https://upload.wikimedia.org/wikipedia/commons/5/5c/Chicago_Bears_logo.svg", "sport": "NFL"},
        {"name": "Cincinnati Bengals", "color": "#FB4F14", "alt": "#000000", "logo": "https://upload.wikimedia.org/wikipedia/commons/8/81/Cincinnati_Bengals_logo.svg", "sport": "NFL"},
        {"name": "Cleveland Browns", "color": "#311D00", "alt": "#FF3C00", "logo": "https://upload.wikimedia.org/wikipedia/en/d/d2/Cleveland_Browns_logo.svg", "sport": "NFL"},
        {"name": "Dallas Cowboys", "color": "#002244", "alt": "#869397", "logo": "https://upload.wikimedia.org/wikipedia/commons/4/4b/Dallas_Cowboys_logo.svg", "sport": "NFL"},
        {"name": "Denver Broncos", "color": "#FB4F14", "alt": "#002244", "logo": "https://upload.wikimedia.org/wikipedia/en/7/76/Denver_Broncos_logo.svg", "sport": "NFL"},
        {"name": "Detroit Lions", "color": "#0076B6", "alt": "#B0B7BC", "logo": "https://upload.wikimedia.org/wikipedia/en/e/e0/Detroit_Lions_logo.svg", "sport": "NFL"},
        {"name": "Green Bay Packers", "color": "#203731", "alt": "#FFB612", "logo": "https://upload.wikimedia.org/wikipedia/commons/5/50/Green_Bay_Packers_logo.svg", "sport": "NFL"},
        {"name": "Houston Texans", "color": "#03202F", "alt": "#A71930", "logo": "https://upload.wikimedia.org/wikipedia/en/2/28/Houston_Texans_logo.svg", "sport": "NFL"},
        {"name": "Indianapolis Colts", "color": "#002C5F", "alt": "#FFFFFF", "logo": "https://upload.wikimedia.org/wikipedia/commons/0/00/Indianapolis_Colts_logo.svg", "sport": "NFL"},
        {"name": "Jacksonville Jaguars", "color": "#006778", "alt": "#000000", "logo": "https://upload.wikimedia.org/wikipedia/en/7/7e/Jacksonville_Jaguars_logo.svg", "sport": "NFL"},
        {"name": "Kansas City Chiefs", "color": "#E31837", "alt": "#FFB81C", "logo": "https://upload.wikimedia.org/wikipedia/en/e/e1/Kansas_City_Chiefs_logo.svg", "sport": "NFL"},
        {"name": "Las Vegas Raiders", "color": "#000000", "alt": "#A5ACAF", "logo": "https://upload.wikimedia.org/wikipedia/en/4/47/Las_Vegas_Raiders_logo.svg", "sport": "NFL"},
        {"name": "Los Angeles Chargers", "color": "#0080C6", "alt": "#FFC20E", "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/7/72/Los_Angeles_Chargers_logo.svg/1200px-Los_Angeles_Chargers_logo.svg.png", "sport": "NFL"},
        {"name": "Los Angeles Rams", "color": "#003594", "alt": "#FFD100", "logo": "https://upload.wikimedia.org/wikipedia/en/8/8e/Los_Angeles_Rams_logo.svg", "sport": "NFL"},
        {"name": "Miami Dolphins", "color": "#008E97", "alt": "#FC4C02", "logo": "https://upload.wikimedia.org/wikipedia/en/3/37/Miami_Dolphins_logo.svg", "sport": "NFL"},
        {"name": "Minnesota Vikings", "color": "#4F2683", "alt": "#FFC62F", "logo": "https://upload.wikimedia.org/wikipedia/en/4/4f/Minnesota_Vikings_logo.svg", "sport": "NFL"},
        {"name": "New England Patriots", "color": "#002244", "alt": "#C60C30", "logo": "https://upload.wikimedia.org/wikipedia/en/b/b9/New_England_Patriots_logo.svg", "sport": "NFL"},
        {"name": "New Orleans Saints", "color": "#D3BC8D", "alt": "#000000", "logo": "https://upload.wikimedia.org/wikipedia/commons/5/50/New_Orleans_Saints_logo.svg", "sport": "NFL"},
        {"name": "New York Giants", "color": "#0B2265", "alt": "#A71930", "logo": "https://upload.wikimedia.org/wikipedia/commons/f/f6/New_York_Giants_logo.svg", "sport": "NFL"},
        {"name": "New York Jets", "color": "#125740", "alt": "#FFFFFF", "logo": "https://upload.wikimedia.org/wikipedia/en/6/6b/New_York_Jets_logo.svg", "sport": "NFL"},
        {"name": "Philadelphia Eagles", "color": "#004C54", "alt": "#A5ACAF", "logo": "https://upload.wikimedia.org/wikipedia/en/8/8e/Philadelphia_Eagles_logo.svg", "sport": "NFL"},
        {"name": "Pittsburgh Steelers", "color": "#000000", "alt": "#FFB612", "logo": "https://upload.wikimedia.org/wikipedia/commons/d/de/Pittsburgh_Steelers_logo.svg", "sport": "NFL"},
        {"name": "San Francisco 49ers", "color": "#AA0000", "alt": "#B3995D", "logo": "https://upload.wikimedia.org/wikipedia/commons/3/3a/San_Francisco_49ers_logo.svg", "sport": "NFL"},
        {"name": "Seattle Seahawks", "color": "#69BE28", "alt": "#002244", "logo": "https://upload.wikimedia.org/wikipedia/en/8/8e/Seattle_Seahawks_logo.svg", "sport": "NFL"},
        {"name": "Tampa Bay Buccaneers", "color": "#D50A0A", "alt": "#767676", "logo": "https://upload.wikimedia.org/wikipedia/en/a/a2/Tampa_Bay_Buccaneers_logo.svg", "sport": "NFL"},
        {"name": "Tennessee Titans", "color": "#0C2340", "alt": "#C8102E", "logo": "https://upload.wikimedia.org/wikipedia/en/c/c1/Tennessee_Titans_logo.svg", "sport": "NFL"},
        {"name": "Washington Commanders", "color": "#5A1414", "alt": "#FFB612", "logo": "https://upload.wikimedia.org/wikipedia/en/d/d6/Washington_Commanders_logo.svg", "sport": "NFL"},

        # NBA
        {"name": "Atlanta Hawks", "color": "#E03A3E", "alt": "#C1D32F", "logo": "https://upload.wikimedia.org/wikipedia/en/2/24/Atlanta_Hawks_logo.svg", "sport": "NBA"},
        {"name": "Boston Celtics", "color": "#008348", "alt": "#BB9753", "logo": "https://upload.wikimedia.org/wikipedia/en/8/8f/Boston_Celtics.svg", "sport": "NBA"},
        {"name": "Brooklyn Nets", "color": "#000000", "alt": "#FFFFFF", "logo": "https://upload.wikimedia.org/wikipedia/commons/4/44/Brooklyn_Nets_newlogo.svg", "sport": "NBA"},
        {"name": "Charlotte Hornets", "color": "#00788C", "alt": "#1D1160", "logo": "https://upload.wikimedia.org/wikipedia/en/c/c4/Charlotte_Hornets_%282014%29_logo.svg", "sport": "NBA"},
        {"name": "Chicago Bulls", "color": "#CE1141", "alt": "#000000", "logo": "https://upload.wikimedia.org/wikipedia/en/6/67/Chicago_Bulls_logo.svg", "sport": "NBA"},
        {"name": "Cleveland Cavaliers", "color": "#6F263D", "alt": "#FDBB30", "logo": "https://upload.wikimedia.org/wikipedia/en/4/4b/Cleveland_Cavaliers_logo.svg", "sport": "NBA"},
        {"name": "Dallas Mavericks", "color": "#00538C", "alt": "#B8C4CA", "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/9/97/Dallas_Mavericks_logo.svg/1200px-Dallas_Mavericks_logo.svg.png", "sport": "NBA"},
        {"name": "Denver Nuggets", "color": "#0E2240", "alt": "#FEC524", "logo": "https://upload.wikimedia.org/wikipedia/en/7/76/Denver_Nuggets.svg", "sport": "NBA"},
        {"name": "Detroit Pistons", "color": "#C8102E", "alt": "#1D42BA", "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/1/1e/Detroit_Pistons_logo.svg/1200px-Detroit_Pistons_logo.svg.png", "sport": "NBA"},
        {"name": "Golden State Warriors", "color": "#006BB6", "alt": "#FDB927", "logo": "https://upload.wikimedia.org/wikipedia/en/0/01/Golden_State_Warriors_logo.svg", "sport": "NBA"},
        {"name": "Houston Rockets", "color": "#CE1141", "alt": "#000000", "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/2/28/Houston_Rockets.svg/1200px-Houston_Rockets.svg.png", "sport": "NBA"},
        {"name": "Indiana Pacers", "color": "#002D62", "alt": "#FDBB30", "logo": "https://upload.wikimedia.org/wikipedia/en/1/1e/Indiana_Pacers_logo.svg", "sport": "NBA"},
        {"name": "Los Angeles Clippers", "color": "#C8102E", "alt": "#1D428A", "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/0/01/Los_Angeles_Clippers_logo.svg/1200px-Los_Angeles_Clippers_logo.svg.png", "sport": "NBA"},
        {"name": "Los Angeles Lakers", "color": "#552583", "alt": "#FDB927", "logo": "https://upload.wikimedia.org/wikipedia/commons/3/3c/Los_Angeles_Lakers_logo.svg", "sport": "NBA"},
        {"name": "Memphis Grizzlies", "color": "#5D76A9", "alt": "#121737", "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/f/f1/Memphis_Grizzlies.svg/1200px-Memphis_Grizzlies.svg.png", "sport": "NBA"},
        {"name": "Miami Heat", "color": "#98002B", "alt": "#000000", "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/f/f3/Miami_Heat_logo.svg/1200px-Miami_Heat_logo.svg.png", "sport": "NBA"},
        {"name": "Milwaukee Bucks", "color": "#00471B", "alt": "#EEE1C6", "logo": "https://upload.wikimedia.org/wikipedia/en/4/4a/Milwaukee_Bucks_logo.svg", "sport": "NBA"},
        {"name": "Minnesota Timberwolves", "color": "#0C2340", "alt": "#78BE20", "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/c/c2/Minnesota_Timberwolves_logo.svg/1200px-Minnesota_Timberwolves_logo.svg.png", "sport": "NBA"},
        {"name": "New Orleans Pelicans", "color": "#0C2340", "alt": "#B4975A", "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/0/0d/New_Orleans_Pelicans_logo.svg/1200px-New_Orleans_Pelicans_logo.svg.png", "sport": "NBA"},
        {"name": "New York Knicks", "color": "#006BB6", "alt": "#F58426", "logo": "https://upload.wikimedia.org/wikipedia/en/2/25/New_York_Knicks_logo.svg", "sport": "NBA"},
        {"name": "Oklahoma City Thunder", "color": "#007AC1", "alt": "#EF3B24", "logo": "https://upload.wikimedia.org/wikipedia/en/5/5d/Oklahoma_City_Thunder.svg", "sport": "NBA"},
        {"name": "Orlando Magic", "color": "#0077C0", "alt": "#000000", "logo": "https://upload.wikimedia.org/wikipedia/en/1/10/Orlando_Magic_logo.svg", "sport": "NBA"},
        {"name": "Philadelphia 76ers", "color": "#006BB6", "alt": "#ED174C", "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/0/0e/Philadelphia_76ers_logo.svg/1200px-Philadelphia_76ers_logo.svg.png", "sport": "NBA"},
        {"name": "Phoenix Suns", "color": "#1D1160", "alt": "#E56020", "logo": "https://upload.wikimedia.org/wikipedia/en/d/dc/Phoenix_Suns_logo.svg", "sport": "NBA"},
        {"name": "Portland Trail Blazers", "color": "#E03A3E", "alt": "#000000", "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/2/21/Portland_Trail_Blazers_logo.svg/1200px-Portland_Trail_Blazers_logo.svg.png", "sport": "NBA"},
        {"name": "Sacramento Kings", "color": "#5A2D81", "alt": "#000000", "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/c/c7/Sacramento_Kings_logo.svg/1200px-Sacramento_Kings_logo.svg.png", "sport": "NBA"},
        {"name": "San Antonio Spurs", "color": "#000000", "alt": "#C4CED4", "logo": "https://upload.wikimedia.org/wikipedia/en/a/a2/San_Antonio_Spurs.svg", "sport": "NBA"},
        {"name": "Toronto Raptors", "color": "#CE1141", "alt": "#000000", "logo": "https://upload.wikimedia.org/wikipedia/en/3/36/Toronto_Raptors_logo.svg", "sport": "NBA"},
        {"name": "Utah Jazz", "color": "#002B5C", "alt": "#00471B", "logo": "https://upload.wikimedia.org/wikipedia/en/0/04/Utah_Jazz_logo_%282022%29.svg", "sport": "NBA"},
        {"name": "Washington Wizards", "color": "#002B5C", "alt": "#E31837", "logo": "https://upload.wikimedia.org/wikipedia/en/0/02/Washington_Wizards_logo.svg", "sport": "NBA"}
    ]

    with app.app_context():
        print("Starting team seeding...")
        count = 0
        updated = 0
        
        for t_data in teams_data:
            team_name = t_data['name']
            sport = t_data['sport']
            
            # Determine Abbreviation
            abbr = None
            if sport == 'NFL':
                abbr = nfl_abbr.get(team_name)
            elif sport == 'NBA':
                abbr = nba_abbr.get(team_name)
            
            if not abbr:
                print(f"Warning: No abbreviation found for {team_name}")
                abbr = team_name[:3].upper()

            # Check if team exists
            team = Team.query.filter_by(team_name=team_name, sport=sport).first()
            
            if team:
                # Update existing
                team.color = t_data['color']
                team.alternate_color = t_data['alt']
                team.logo_url = t_data['logo']
                team.team_abbr = abbr
                updated += 1
            else:
                # Create new
                team = Team(
                    team_name=team_name,
                    team_abbr=abbr,
                    sport=sport,
                    color=t_data['color'],
                    alternate_color=t_data['alt'],
                    logo_url=t_data['logo'],
                    team_name_short=team_name.split()[-1] # e.g. "Lions"
                )
                db.session.add(team)
                count += 1
        
        try:
            db.session.commit()
            print(f"Seeding complete. Created {count} new teams, updated {updated} existing teams.")
        except Exception as e:
            db.session.rollback()
            print(f"Error seeding teams: {e}")

if __name__ == "__main__":
    seed_teams()
