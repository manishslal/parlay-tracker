
import requests

def check_endpoint(sport, league):
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/teams"
    print(f"Checking {league.upper()} ({url})...")
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            count = len(data.get('sports', [])[0].get('leagues', [])[0].get('teams', []))
            print(f"  ✅ Success! Found {count} teams.")
            return True
        else:
            print(f"  ❌ Failed with status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

if __name__ == "__main__":
    check_endpoint("football", "nfl")
    check_endpoint("basketball", "nba")
    check_endpoint("baseball", "mlb")
    check_endpoint("hockey", "nhl")
