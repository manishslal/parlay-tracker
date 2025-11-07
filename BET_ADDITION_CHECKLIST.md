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
  - `"Dabble"` - Shows Dabble logo
- **Auto-Detection**: Can be inferred from bet_id:
  - If bet_id starts with `"O/"` → FanDuel
  - If bet_id starts with `"DK"` → DraftKings
- **Displays**: Footer logo and site name
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
- **Common Values**:
  - Player Stats: `"passing_yards"`, `"rushing_yards"`, `"receiving_yards"`, `"receptions"`, `"anytime_touchdown"`
  - Team Stats: `"moneyline"`, `"spread"`, `"total_points"`, `"total_points_over"`, `"total_points_under"`
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

---

## 🔍 Validation Checklist

Before submitting the bet insertion script, verify:

### Bet-Level Validation
- [ ] `bet_id` is present and matches betting site format
- [ ] `name` is descriptive and identifies the bet
- [ ] `type` is one of: `"Same Game Parlay"`, `"Parlay"`, or `"Single Bet"`
- [ ] `betting_site` is one of: `"FanDuel"`, `"DraftKings"`, or `"Dabble"`
- [ ] `bet_date` is in `YYYY-MM-DD` format
- [ ] `wager` is a string with decimal (e.g., `"10.00"`)
- [ ] `odds` includes + or - prefix (e.g., `"+442"`)
- [ ] `returns` is calculated correctly (payout - wager)
- [ ] `legs` array has at least one leg

### Leg-Level Validation (for each leg)
- [ ] `away` team name matches ESPN's full team name
- [ ] `home` team name matches ESPN's full team name
- [ ] `game_date` is in `YYYY-MM-DD` format and matches the game date
- [ ] `stat` is a valid stat type
- [ ] `target` is a number (can be decimal for half-points)
- [ ] `team` is present and matches `away` or `home`
- [ ] `player` is present if it's a player prop bet
- [ ] `position` is included for all player prop bets

### Special Cases
- [ ] **Same Game Parlay**: All legs have the same `away`, `home`, and `game_date`
- [ ] **Moneyline bets**: `target` is `0`
- [ ] **Spread bets**: `target` is the spread value (positive or negative)
- [ ] **Team verification**: Player's team matches the correct team (check rosters!)

---

## 🚨 Common Mistakes to Avoid

### 1. Missing `bet_date`
- **Symptom**: Date shows as "N/A" in header
- **Fix**: Add `"bet_date": "YYYY-MM-DD"` at bet level

### 2. Missing `betting_site`
- **Symptom**: Logo doesn't display, site shows "N/A"
- **Fix**: Add `"betting_site": "FanDuel"` (or DraftKings/Dabble)

### 3. Wrong player team
- **Symptom**: Stats don't update during game
- **Fix**: Verify player's team matches ESPN roster

### 4. Missing `position`
- **Symptom**: Position badge doesn't show
- **Fix**: Add `"position": "WR"` (or QB/RB/TE/etc.)

### 5. Inconsistent team names
- **Symptom**: Scoreboard doesn't appear
- **Fix**: Use full ESPN team names (e.g., "Las Vegas Raiders", not "Raiders")

### 6. Wrong `game_date`
- **Symptom**: Game data doesn't load
- **Fix**: Verify the actual game date in `YYYY-MM-DD` format

### 7. Missing `type` field
- **Symptom**: Scoreboard display issues, wrong formatting
- **Fix**: Add `"type": "Same Game Parlay"` or `"Parlay"`

---

## 📝 Example Template

```python
bet_data = {
    # Bet-level fields
    "bet_id": "O/0240915/0000068",           # Required: Unique identifier
    "name": "Player Name Parlay",             # Required: Display name
    "type": "Same Game Parlay",               # Required: Bet type
    "betting_site": "FanDuel",                # Required: FanDuel/DraftKings/Dabble
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
            "stat": "receiving_yards",         # Stat type
            "target": 46.5,                    # Target value
            "team": "Las Vegas Raiders",       # Player's team
            
            # Required for player props
            "player": "Tre Tucker",            # Player name
            "position": "WR",                  # Player position
        },
        # ... more legs
    ]
}
```

---

## 🎯 Testing Checklist

After adding a bet, verify:

- [ ] **Bet ID displays** correctly in footer (not "N/A")
- [ ] **Date displays** correctly in header (not "N/A")
- [ ] **Betting site logo** appears in footer
- [ ] **Scoreboard appears** at top (if game is today/live)
- [ ] **All player positions** show correctly
- [ ] **Team names** match in scoreboard and leg rows
- [ ] **Stats update** during live games
- [ ] **Progress bars** display correctly for each leg

---

## 📚 Quick Reference: Team Name Format

Always use ESPN's full team names:

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

---

## 🔄 Workflow Summary

1. **Gather bet information** from betting slip
2. **Identify betting site** (FanDuel/DraftKings/Dabble)
3. **Extract bet-level data** (ID, name, type, date, wager, odds, returns)
4. **Extract each leg's data** (teams, game date, player, position, stat, target)
5. **Verify player teams** using current rosters
6. **Run through validation checklist** above
7. **Add users** (primary bettor + viewers using `add_user()` method)
8. **Test on Render** to verify all displays correctly

---

**Last Updated**: November 6, 2025  
**Version**: 1.0
