# Bet Addition Checklist

Use this checklist every time you add a new bet to ensure all required fields are present and the bet displays correctly on the frontend.

---

## ✅ Required Bet-Level Fields

### 1. **bet_id** (string, required)
- **Purpose**: Unique identifier for the bet, used for display and tracking
- **Format**: Varies by betting site
  - FanDuel: `"O/[numbers]/[numbers]"` (e.g., `"O/0240915/0000068"`)
  - DraftKings: `"DK[numbers]"` (e.g., `"DK63898069623329495"`)
  - Dabble: `"[custom format]"`
- **Displays**: Footer of parlay card ("Bet ID: ...")
- **Example**: `"bet_id": "O/0240915/0000068"`

### 2. **name** (string, required)
- **Purpose**: Display name for the parlay
- **Format**: Descriptive name that identifies the bet
- **Displays**: Header of parlay card
- **Example**: `"name": "Lamar Jackson SGP"`

### 3. **type** (string, required)
- **Purpose**: Type of bet, affects display logic and scoreboard visibility
- **Valid Values**:
  - `"Same Game Parlay"` or `"SGP"` - Single game, shows one scoreboard
  - `"Parlay"` - Multiple games, shows multiple scoreboards
  - `"Single Bet"` - Single leg bet
- **Displays**: Affects header display and scoreboard count
- **Example**: `"type": "Same Game Parlay"`

### 4. **betting_site** (string, required)
- **Purpose**: Betting platform, determines logo display
- **Valid Values**:
  - `"FanDuel"` - Shows FanDuel logo
  - `"DraftKings"` - Shows DraftKings logo
  - `"Bet365"` - Shows Bet365 logo
  - `"Dabble"` - Shows Dabble logo
- **Auto-Detection**: Can be inferred from bet_id:
  - If bet_id starts with `"O/"` → FanDuel
  - If bet_id starts with `"DK"` → DraftKings
- **Displays**: Footer logo and site name (logo changes based on dark/light mode)
- **Example**: `"betting_site": "FanDuel"`

### 5. **bet_date** (string, required, YYYY-MM-DD format)
- **Purpose**: Date of the bet placement, used for sorting and date display
- **Format**: `"YYYY-MM-DD"` (e.g., `"2025-11-06"`)
- **Displays**: Header subtitle with formatted date
- **Example**: `"bet_date": "2025-11-06"`
- **⚠️ Common Issue**: Missing this causes "N/A" to show for date

### 6. **wager** (string, required)
- **Purpose**: Amount wagered on the bet
- **Format**: String with decimal (e.g., `"10.00"`)
- **Displays**: Footer "Wager: $XX.XX"
- **Example**: `"wager": "10.00"`

### 7. **odds** (string, required)
- **Purpose**: American odds format for the bet
- **Format**: String with + or - prefix (e.g., `"+442"`, `"-120"`)
- **Displays**: Footer "Odds: +XXX"
- **Example**: `"odds": "+442"`

### 8. **returns** (string, required)
- **Purpose**: Expected profit (payout minus wager)
- **Format**: String with decimal (e.g., `"44.20"`)
- **Calculation**: `(payout - wager)` or computed from odds
- **Displays**: Footer "Winnings: $XX.XX"
- **Example**: `"returns": "44.20"`

### 9. **legs** (array, required)
- **Purpose**: Individual bets within the parlay
- **Format**: Array of leg objects (see Leg-Level Fields below)
- **Minimum**: 1 leg for single bets
- **Displays**: Table rows in parlay card
- **Example**: `"legs": [...]`

---

## ✅ Required Leg-Level Fields

Each leg object in the `legs` array must contain:

### 1. **away** (string, required)
- **Purpose**: Away team full name
- **Format**: Full team name (e.g., `"Las Vegas Raiders"`)
- **Used For**: Game matching, scoreboard display
- **Example**: `"away": "Las Vegas Raiders"`

### 2. **home** (string, required)
- **Purpose**: Home team full name
- **Format**: Full team name (e.g., `"Denver Broncos"`)
- **Used For**: Game matching, scoreboard display
- **Example**: `"home": "Denver Broncos"`

### 3. **game_date** (string, required, YYYY-MM-DD format)
- **Purpose**: Date of the game
- **Format**: `"YYYY-MM-DD"` (e.g., `"2025-11-06"`)
- **Used For**: ESPN API fetching, game status tracking
- **Example**: `"game_date": "2025-11-06"`

### 4. **stat** (string, required)
- **Purpose**: Type of statistic being bet on
- **⚠️ CRITICAL**: Must be lowercase for live data to work correctly
- **Common Values**:
  - Player Stats: `"passing_yards"`, `"rushing_yards"`, `"receiving_yards"`, `"rushing_receiving_yards"`, `"receptions"`, `"anytime_touchdown"`
  - Team Stats: `"moneyline"`, `"spread"`, `"total_points"`, `"total_points_over"`, `"total_points_under"`
- **Invalid Values** (will break live updates):
  - ❌ `"SPREAD"` (uppercase)
  - ❌ `"PLAYER_PROP"` (generic)
  - ❌ `"MONEYLINE"` (uppercase)
- **Displays**: Leg description in table
- **Example**: `"stat": "receiving_yards"`

### 5. **target** (number, required)
- **Purpose**: Target value for the stat
- **Format**: Number (can be float for half-points)
- **Special Cases**:
  - Moneyline: `0` (no target, just win/loss)
  - Anytime TD: `1` (one touchdown)
  - Spread: Positive or negative number
- **Displays**: Target value in leg row
- **Example**: `"target": 46.5`

### 6. **team** (string, conditionally required)
- **Purpose**: Team the player plays for (or team being bet on)
- **Required When**:
  - Player prop bets (always)
  - Team bets (moneyline, spread)
- **Format**: Full team name matching away/home
- **Example**: `"team": "Las Vegas Raiders"`

### 7. **player** (string, conditionally required)
- **Purpose**: Player name for player prop bets
- **Required When**: Betting on a player stat (not team stats)
- **Format**: Full player name (e.g., `"Tre Tucker"`)
- **Not Required For**: Moneyline, spread, totals
- **Displays**: Player name in leg row
- **Example**: `"player": "Tre Tucker"`

### 8. **position** (string, recommended)
- **Purpose**: Player's position
- **Format**: Standard abbreviation
- **Valid Values**: `"QB"`, `"RB"`, `"WR"`, `"TE"`, `"K"`, `"DEF"`, etc.
- **Displays**: Position badge next to player name
- **Example**: `"position": "WR"`
- **⚠️ Note**: While not strictly required, adds clarity to the UI

### 9. **sport** (string, required for multi-sport support)
- **Purpose**: Identifies which sport API to use for fetching game data
- **Format**: Uppercase sport code
- **Valid Values**: `"NFL"`, `"NBA"`, `"MLB"`, `"NHL"`, `"NCAAF"`, `"NCAAB"`
- **Default**: `"NFL"` (if omitted)
- **Used For**: ESPN API routing, game data fetching
- **Example**: `"sport": "NBA"`
- **⚠️ Important**: Required for non-NFL games to fetch live data correctly

---

## 🔍 Validation Checklist

Before submitting the bet insertion script, verify:

### Bet-Level Validation
- [ ] `bet_id` is present and matches betting site format
- [ ] `name` is descriptive and identifies the bet
- [ ] `type` is one of: `"Same Game Parlay"`, `"Parlay"`, or `"Single Bet"`
- [ ] `betting_site` is one of: `"FanDuel"`, `"DraftKings"`, `"Bet365"`, or `"Dabble"`
- [ ] `bet_date` is in `YYYY-MM-DD` format
- [ ] `wager` is a string with decimal (e.g., `"10.00"`)
- [ ] `odds` includes + or - prefix (e.g., `"+442"`)
- [ ] `returns` is calculated correctly (payout - wager)
- [ ] `legs` array has at least one leg

### Leg-Level Validation (for each leg)
- [ ] `away` team name matches ESPN's full team name
- [ ] `home` team name matches ESPN's full team name
- [ ] `game_date` is in `YYYY-MM-DD` format and matches the game date
- [ ] `stat` is **lowercase** and specific (not generic like "PLAYER_PROP")
- [ ] `target` is a number (can be decimal for half-points)
- [ ] `team` is present and matches `away` or `home`
- [ ] `player` is present if it's a player prop bet
- [ ] `position` is included for all player prop bets
- [ ] `sport` is included for non-NFL games (NBA, MLB, NHL, etc.)

### Special Cases
- [ ] **Same Game Parlay**: All legs have the same `away`, `home`, and `game_date`
- [ ] **Moneyline bets**: `target` is `0`
- [ ] **Spread bets**: `target` is the spread value (positive or negative)
- [ ] **Team verification**: Player's team matches the correct team (check rosters!)

---

## 🚨 Common Mistakes to Avoid

### 1. **CRITICAL**: Uppercase `stat` values
- **Symptom**: Status shows "Not Started", current value is 0, live data doesn't update
- **Why**: Backend calculations only work with lowercase stat names
- **Fix**: Change `"SPREAD"` → `"spread"`, `"MONEYLINE"` → `"moneyline"`, `"PLAYER_PROP"` → specific stat like `"rushing_receiving_yards"`
- **Example Fix**:
  ```python
  # ❌ WRONG - Won't fetch live data
  "stat": "SPREAD"
  
  # ✅ CORRECT - Will fetch live data
  "stat": "spread"
  ```

### 2. Generic stat types (e.g., "PLAYER_PROP")
- **Symptom**: Bet type shows as "PLAYER PROP" instead of actual stat name
- **Why**: Frontend needs specific stat to display correctly
- **Fix**: Use specific stat names: `"rushing_yards"`, `"receiving_yards"`, `"rushing_receiving_yards"`, `"passing_yards"`, etc.
- **Example Fix**:
  ```python
  # ❌ WRONG
  "stat": "PLAYER_PROP"
  
  # ✅ CORRECT
  "stat": "rushing_receiving_yards"
  ```

### 3. Missing `sport` for non-NFL games
- **Symptom**: NBA/MLB/NHL games show 0-0 scores, no live data updates
- **Why**: System defaults to NFL API if sport is not specified
- **Fix**: Add `"sport": "NBA"` (or MLB/NHL/NCAAF/NCAAB) to each leg
- **Example Fix**:
  ```python
  # For NBA game
  {
      "away": "Oklahoma City Thunder",
      "home": "Memphis Grizzlies",
      "sport": "NBA",  # ✅ Required for non-NFL
      "stat": "moneyline",
      "target": 0
  }
  ```

### 4. Wrong home/away team order
- **Symptom**: Spread calculations are inverted, scores don't match
- **Why**: ESPN API has specific home/away designations
- **Fix**: Verify home/away teams match ESPN's game page exactly
- **How to Check**: Look at ESPN scoreboard - away team is always listed first

### 5. Missing `bet_date`
- **Symptom**: Date shows as "N/A" in header
- **Fix**: Add `"bet_date": "YYYY-MM-DD"` at bet level

### 6. Missing `betting_site`
- **Symptom**: Logo doesn't display, site shows "N/A"
- **Fix**: Add `"betting_site": "FanDuel"` (or DraftKings/Bet365/Dabble)

### 7. Wrong player team
- **Symptom**: Stats don't update during game
- **Fix**: Verify player's team matches ESPN roster

### 8. Missing `position`
- **Symptom**: Position badge doesn't show
- **Fix**: Add `"position": "WR"` (or QB/RB/TE/etc.)

### 9. Inconsistent team names
- **Symptom**: Scoreboard doesn't appear, team names show as abbreviations
- **Fix**: Use full ESPN team names (e.g., "Las Vegas Raiders", not "Raiders" or "LV")
- **Note**: System now auto-updates team names from ESPN, but correct initial names help matching

### 10. Wrong `game_date`
- **Symptom**: Game data doesn't load
- **Fix**: Verify the actual game date in `YYYY-MM-DD` format

### 11. Missing `type` field
- **Symptom**: Scoreboard display issues, wrong formatting
- **Fix**: Add `"type": "Same Game Parlay"` or `"Parlay"`

---

## 📝 Example Templates

### NFL Player Prop Parlay
```python
bet_data = {
    # Bet-level fields
    "bet_id": "O/0240915/0000068",           # Required: Unique identifier
    "name": "Player Name Parlay",             # Required: Display name
    "type": "Same Game Parlay",               # Required: Bet type
    "betting_site": "FanDuel",                # Required: FanDuel/DraftKings/Bet365/Dabble
    "bet_date": "2025-11-06",                 # Required: YYYY-MM-DD format
    "wager": "10.00",                         # Required: Amount wagered
    "odds": "+442",                           # Required: American odds
    "returns": "44.20",                       # Required: Expected profit
    
    # Legs array
    "legs": [
        {
            # Required for all legs
            "away": "Las Vegas Raiders",       # Full team name
            "home": "Denver Broncos",          # Full team name
            "game_date": "2025-11-06",         # YYYY-MM-DD format
            "stat": "receiving_yards",         # ⚠️ LOWERCASE stat name
            "target": 46.5,                    # Target value
            "team": "Las Vegas Raiders",       # Player's team
            "sport": "NFL",                    # Sport code (optional for NFL)
            
            # Required for player props
            "player": "Tre Tucker",            # Player name
            "position": "WR",                  # Player position
        },
        # ... more legs
    ]
}
```

### NFL Spread Bet
```python
{
    "away": "Buffalo Bills",
    "home": "Miami Dolphins",
    "game_date": "2025-11-03",
    "stat": "spread",                    # ⚠️ lowercase "spread" not "SPREAD"
    "target": -3.5,                      # Spread value (negative for favorites)
    "team": "Buffalo Bills",             # Team being bet on
    "sport": "NFL"
}
```

### NBA Moneyline Bet
```python
{
    "away": "Oklahoma City Thunder",
    "home": "Memphis Grizzlies",
    "game_date": "2025-11-03",
    "stat": "moneyline",                 # ⚠️ lowercase "moneyline" not "MONEYLINE"
    "target": 0,                         # Always 0 for moneyline
    "team": "Oklahoma City Thunder",     # Team being bet on
    "sport": "NBA"                       # ⚠️ REQUIRED for non-NFL games
}
```

### Combined Stats (Rush + Rec Yards)
```python
{
    "away": "Detroit Lions",
    "home": "Washington Commanders",
    "game_date": "2025-11-03",
    "stat": "rushing_receiving_yards",   # ⚠️ Specific stat, not "PLAYER_PROP"
    "target": 100.5,
    "team": "Detroit Lions",
    "player": "Jahmyr Gibbs",
    "position": "RB",
    "sport": "NFL"
}
```

---

## 🎯 Testing Checklist

After adding a bet, verify on the frontend:

### Display Tests
- [ ] **Bet ID displays** correctly in footer (not "N/A")
- [ ] **Date displays** correctly in header (not "N/A")
- [ ] **Betting site logo** appears in footer
- [ ] **Scoreboard appears** at top (if game is today/live)
- [ ] **All player positions** show correctly
- [ ] **Team names** show full names (e.g., "Grizzlies" not "MEM", "Commanders" not "WSH")
- [ ] **Bet type** shows specific stat name (e.g., "Rush + Rec Yds" not "PLAYER PROP")

### Live Data Tests (for active games)
- [ ] **Status updates** from "Not Started" → "In Progress" → "Hit"/"Miss"
- [ ] **Scores display** correctly for all games (not 0-0)
- [ ] **Current values** populate and update during game
- [ ] **Progress bars** display correctly for each leg
- [ ] **Score differentials** show for spread/moneyline bets
- [ ] **Multi-sport games** (NBA, MLB, NHL) fetch data correctly

### Backend Verification
```python
# Test query to verify bet data
python3 -c "
from app import db, Bet, BetLeg
bet = Bet.query.filter_by(bet_id='YOUR_BET_ID').first()
for leg in bet.bet_legs:
    print(f'Leg: {leg.player or leg.team}')
    print(f'  Stat: {leg.bet_type} (should be lowercase)')
    print(f'  Sport: {leg.sport or \"NFL\"}')
    print(f'  Away: {leg.away_team}, Home: {leg.home_team}')
"
```

---

## 📚 Quick Reference: Team Name Format

Always use ESPN's full team names for database insertion. The system will auto-update display names from ESPN API, but correct initial names help with game matching:

### NFL Teams
| Correct ✅ | Incorrect ❌ |
|-----------|-------------|
| Las Vegas Raiders | Raiders, LV Raiders |
| Denver Broncos | Broncos |
| Baltimore Ravens | Ravens |
| Minnesota Vikings | Vikings |
| Los Angeles Rams | LA Rams, Rams |
| Los Angeles Chargers | LA Chargers, Chargers |
| New York Giants | NY Giants, Giants |
| New York Jets | NY Jets, Jets |
| Buffalo Bills | Bills |
| Miami Dolphins | Dolphins |
| Detroit Lions | Lions |
| Washington Commanders | Commanders, Football Team, Redskins |

### NBA Teams
| Correct ✅ | Incorrect ❌ |
|-----------|-------------|
| Oklahoma City Thunder | Thunder, OKC |
| Memphis Grizzlies | Grizzlies, MEM |
| Los Angeles Lakers | Lakers, LAL |
| Los Angeles Clippers | Clippers, LAC |
| Golden State Warriors | Warriors, GSW |
| New York Knicks | Knicks, NYK |

### MLB Teams
| Correct ✅ | Incorrect ❌ |
|-----------|-------------|
| New York Yankees | Yankees, NYY |
| Los Angeles Dodgers | Dodgers, LAD |
| Boston Red Sox | Red Sox, BOS |

### NHL Teams
| Correct ✅ | Incorrect ❌ |
|-----------|-------------|
| Vegas Golden Knights | Golden Knights, VGK |
| Tampa Bay Lightning | Lightning, TBL |
| Toronto Maple Leafs | Maple Leafs, TOR |

---

## 🔄 Workflow Summary

1. **Gather bet information** from betting slip
2. **Identify betting site** (FanDuel/DraftKings/Bet365/Dabble)
3. **Extract bet-level data** (ID, name, type, date, wager, odds, returns)
4. **Extract each leg's data** (teams, game date, player, position, stat, target, sport)
5. **Verify home/away teams** match ESPN's game page exactly
6. **Verify player teams** using current rosters
7. **Convert all stat types to lowercase** (spread, moneyline, rushing_yards, etc.)
8. **Use specific stat names** instead of generic types (rushing_receiving_yards, not PLAYER_PROP)
9. **Add sport field** for non-NFL games (NBA, MLB, NHL, NCAAF, NCAAB)
10. **Run through validation checklist** above
11. **Add bet sharing** (NEW V2 system):
    - Primary bettor is set via `Bet(user_id=primary_user.id)`
    - Add secondary bettors: `bet.add_secondary_bettor(user_id)` (can edit/place bet)
    - Add watchers: `bet.add_watcher(user_id)` (can only view bet)
    - ⚠️ OLD METHOD DEPRECATED: Don't use `add_user()` anymore
12. **Test locally** if possible, then push to production
13. **Test on Render** with `use_live_data=true` parameter to verify:
    - Live scores populate correctly
    - Status updates from "Not Started" to "In Progress"
    - Current values calculate correctly
    - Team names display as full names (not abbreviations)
    - Bet types display specific stat names

## 🐛 Debugging Tips

If a bet isn't displaying live data correctly:

1. **Check stat field is lowercase**: `"spread"` not `"SPREAD"`
2. **Check sport field for non-NFL**: Add `"sport": "NBA"` for basketball games
3. **Verify home/away teams**: Check ESPN game page for correct designation
4. **Check game_date format**: Must be `YYYY-MM-DD`
5. **Use API with use_live_data=true**: 
   ```
   https://parlays-tracker.onrender.com/api/parlays?user=USERNAME&use_live_data=true
   ```
6. **Check backend logs** on Render for API errors

## 📊 Key Stat Type Mappings

| Database Value | Frontend Display | Use Case |
|---------------|------------------|----------|
| `spread` | "Spread" | Team spread bets |
| `moneyline` | "Moneyline" | Team win/loss bets |
| `rushing_receiving_yards` | "Rush + Rec Yds" | Combined RB/WR stats |
| `receiving_yards` | "Rec Yds" | Receiving yards only |
| `rushing_yards` | "Rush Yds" | Rushing yards only |
| `passing_yards` | "Pass Yds" | QB passing yards |
| `receptions` | "Receptions" | Number of catches |
| `anytime_touchdown` | "Anytime TD" | Touchdown scorer |

**⚠️ Never use**: `SPREAD`, `MONEYLINE`, `PLAYER_PROP` (uppercase or generic values)

---

## � Bet Sharing V2 System (Updated November 11, 2025)

### Overview
The bet sharing system was migrated from a `bet_users` many-to-many table to PostgreSQL array columns for better performance and simpler code.

### Sharing Roles

1. **Primary Bettor** (set via `user_id`)
   - The main owner of the bet
   - Can edit and view the bet
   - Set when creating: `bet = Bet(user_id=primary_user.id)`
   - Retrieved via: `bet.get_primary_bettor()` → returns username

2. **Secondary Bettors** (stored in `secondary_bettors[]` array)
   - Users who can also place/edit this bet
   - Have full edit permissions like primary bettor
   - Add: `bet.add_secondary_bettor(user_id)`
   - Remove: `bet.remove_secondary_bettor(user_id)`
   - Check: `bet.user_can_edit(user_id)` → returns True for primary + secondary

3. **Watchers** (stored in `watchers[]` array)
   - Users who can only view the bet (read-only)
   - Cannot edit or place the bet
   - Add: `bet.add_watcher(user_id)`
   - Remove: `bet.remove_watcher(user_id)`
   - Check: `bet.user_can_view(user_id)` → returns True for all three roles

### Code Example
```python
# Create bet for primary bettor
manishslal = User.query.filter_by(username='manishslal').first()
etoteja = User.query.filter_by(username='etoteja').first()

bet = Bet(user_id=manishslal.id)  # manishslal is primary bettor
bet.set_bet_data(bet_data)

db.session.add(bet)
db.session.flush()  # Get bet.id

# Add secondary bettor (can edit)
bet.add_secondary_bettor(etoteja.id)

# OR add watcher (view only)
# bet.add_watcher(etoteja.id)

# Add legs
for leg_data in bet_data['legs']:
    leg = BetLeg(...)
    db.session.add(leg)

db.session.commit()
```

### Frontend Visibility
The backend automatically filters bets based on sharing:
- `/live` endpoint shows all bets where `user_id == current_user` OR `current_user in secondary_bettors` OR `current_user in watchers`
- No changes needed in frontend code - the `get_user_bets_query()` function handles filtering

### Migration Notes
- ✅ Migration completed November 11, 2025
- ✅ All 107 shared bets preserved
- ⚠️ OLD METHOD: `bet.add_user(user, is_primary=True/False)` is DEPRECATED
- ⚠️ NEW METHOD: Use `bet.add_secondary_bettor()` or `bet.add_watcher()`

---

## �🚨 Critical Issues Fixed (November 10, 2025)

### Issue 1: Completed Bets Stuck in Live View
- **Symptom**: Bets with finished games remain in "Live Bets" instead of moving to "Historical Bets"
- **Root Cause**: 
  1. `auto_move_completed_bets()` was using `get_bet_data()` which returns empty legs array
  2. Team matching failed because database stores abbreviations (BUF, MIA) but API returns full names
- **Fix Applied**:
  - Changed to use `to_dict_structured(use_live_data=True)` to properly build legs from BetLeg table
  - Added team abbreviations (`away_abbr`, `home_abbr`) to game data structure
  - Updated matching logic to compare both full names and abbreviations
- **Prevention**: Always use team CODES (abbreviations) in database, not full names

### Issue 2: Team Code Storage
- **Best Practice**: Store team abbreviations in `away_team` and `home_team` fields
  - ✅ CORRECT: `"away_team": "PHI"`, `"home_team": "GB"`
  - ❌ WRONG: `"away_team": "Philadelphia Eagles"`, `"home_team": "Green Bay Packers"`
- **Why**: Enables flexible matching between database codes and ESPN API full names
- **Implementation**: The `fetch_game_details_from_espn()` function now returns both formats for matching

### Issue 3: Empty Legs Array in bet_data JSON
- **Symptom**: Newer bets have `"legs": []` in bet_data JSON column
- **Why**: Legs are now stored in BetLeg table, not in JSON
- **Solution**: Always use `to_dict_structured()` method instead of `get_bet_data()` when working with legs
- **Code Example**:
  ```python
  # ❌ WRONG - Returns empty legs array
  bet_data = bet.get_bet_data()
  
  # ✅ CORRECT - Builds legs from BetLeg table
  bet_data = bet.to_dict_structured(use_live_data=True)
  ```

---

**Last Updated**: November 10, 2025  
**Version**: 2.1 - Added critical fixes for auto-move functionality and team code handling
