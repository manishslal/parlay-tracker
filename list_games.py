
from helpers.espn_api import get_espn_games_with_ids_for_date
from datetime import datetime
import pytz

def list_todays_games():
    eastern = pytz.timezone('US/Eastern')
    today = datetime.now(eastern).date()
    print(f"Fetching games for {today}...")
    
    games = get_espn_games_with_ids_for_date(today)
    if games:
        print(f"Found {len(games)} games:")
        for g in games:
            print(f"  - {g}")
    else:
        print("No games found for today.")

if __name__ == "__main__":
    list_todays_games()
