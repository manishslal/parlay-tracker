# Historical Bet Processing Automation

## Overview

This document describes the automated system for processing historical bets in the Parlay Tracker application. The system automatically moves completed bets to historical status and processes them with ESPN API data to populate missing game results and player statistics.

## Architecture

The automation consists of two main phases:

1. **Auto-Archiving**: Moves bets with games 2+ days old to historical status
2. **Historical API Processing**: Fetches ESPN data and updates bet outcomes

## Decision Tree: Auto-Archiving Process (Runs every 5 minutes)

```
START: auto_move_completed_bets()
├── Check all user bets with status ['pending', 'live']
├── For each bet:
│   ├── Get all bet legs
│   ├── Check if ALL game dates are 2+ days in the past
│   │   ├── YES: Move to historical
│   │   │   ├── Set is_active = False
│   │   │   ├── Set status = 'completed'
│   │   │   └── Set api_fetched = 'Yes' (prevents processing)
│   │   └── NO: Continue to live processing
│   └── Process remaining live bets with ESPN data
│       ├── Fetch live game data for each leg
│       ├── Check if ALL games are STATUS_FINAL
│       │   ├── YES: Determine bet outcome
│       │   │   ├── Has confirmed loss? → status = 'lost'
│       │   │   └── No losses? → status = 'won'
│       │   └── NO: Keep as live/pending
└── Commit changes
```

## Decision Tree: Historical API Processing (Runs every hour)

```
START: process_historical_bets_api()
├── Query database for historical bets
│   Criteria: is_active=False AND is_archived=False AND api_fetched='No'
├── Any bets found?
│   ├── NO: Exit (nothing to process)
│   └── YES: Process each bet
│       └── For each bet:
│           ├── Get all bet_legs
│           ├── Any legs found?
│           │   ├── NO: Log issue "No legs found" → Skip bet
│           │   └── YES: Process each leg
│           │       ├── Step 3a: Link Player to Leg
│           │       │   ├── Has player_name?
│           │       │   │   ├── NO: Skip linking (team bet)
│           │       │   │   └── YES: Search Player table
│           │       │   │       ├── Match found by name?
│           │       │   │   │   ├── YES: Set player_id + position
│           │       │   │   │   └── NO: Log issue → Mark leg failed
│           │       ├── Step 3d: Fetch ESPN Game Data
│           │       │   ├── Call espn_api.get_espn_game_data()
│           │       │   │   ├── Game data found?
│           │       │   │   │   ├── YES: Update leg with:
│           │       │   │   │   │   ├── achieved_value
│           │       │   │   │   │   ├── home_score, away_score
│           │       │   │   │   │   ├── is_home_game, game_id
│           │       │   │   │   └── NO: Log issue → Mark leg failed
│           │       ├── Step 3e: Update Leg Status
│           │       │   ├── Set game_status = 'STATUS_FINAL'
│           │       │   ├── Has achieved_value AND target_value?
│           │       │   │   ├── YES: Determine hit/miss
│           │       │   │   │   ├── moneyline: achieved_value > 0
│           │       │   │   │   ├── spread: (achieved_value + target_value) > 0
│           │       │   │   │   ├── total_points/player_prop:
│           │       │   │   │   │   ├── under: achieved_value < target_value
│           │       │   │   │   │   └── over: achieved_value >= target_value
│           │       │   │   │   └── Set status = 'won'/'lost', is_hit = True/False
│           │       │   │   └── NO: Set status = 'pending', is_hit = None
│           ├── All legs processed successfully?
│           │   ├── YES: Mark bet complete
│           │   │   ├── Set api_fetched = 'Yes'
│           │   │   └── Set last_api_update = now()
│           │   └── NO: Keep api_fetched = 'No' for retry
│           └── Log all issues to Issues page
└── Commit all changes
```

## Key Components

### Database Fields
- `Bet.is_active`: False for historical bets
- `Bet.is_archived`: False for bets that should be processed
- `Bet.api_fetched`: 'No' for unprocessed, 'Yes' for processed
- `Bet.last_api_update`: Timestamp of last processing

### Bet Selection Criteria
Historical bets are selected using:
```sql
is_active=False AND is_archived=False AND api_fetched='No'
```

### Player Linking Logic
When processing player bets, the system searches the Player table by:
1. Exact match on `player_name`
2. Exact match on `normalized_name`
3. Exact match on `display_name`
4. Filtered by matching `sport`

### ESPN Data Fetching
- Converts game dates to YYYY-MM-DD format
- Queries ESPN scoreboard API for matching team games
- Returns final scores, game IDs, and player statistics

### Bet Outcome Determination
- **Moneyline**: `achieved_value > 0`
- **Spread**: `(achieved_value + target_value) > 0`
- **Total Points/Player Props**:
  - Under: `achieved_value < target_value`
  - Over: `achieved_value >= target_value`

## Automation Schedule

| Process | Frequency | Description |
|---------|-----------|-------------|
| Auto-archiving | Every 5 minutes | Moves old bets to historical |
| Historical processing | Every hour | Processes historical bets with ESPN data |
| Live bet updates | Every minute | Updates active bets with live data |
| Leg status updates | Every 10 minutes | Determines hit/miss for completed legs |

## Error Handling

### Issue Logging
- Individual leg failures don't stop bet processing
- All issues are logged to the Issues page with specific details
- Failed bets remain `api_fetched = 'No'` for retry on next cycle

### Common Issues
1. **Player not found**: Player name doesn't match any in database
2. **ESPN data not found**: Game not found in ESPN API (wrong date/teams)
3. **API errors**: ESPN API unavailable or rate limited
4. **Date parsing errors**: Invalid game date format

### Recovery
- Failed bets are retried on the next hourly cycle
- Issues page provides visibility into specific failures
- Manual intervention may be needed for data corrections

## Files Involved

- `automation/historical_bet_processing.py`: Main processing logic
- `helpers/database.py`: Auto-archiving logic
- `helpers/espn_api.py`: ESPN data fetching
- `routes/bets.py`: Issues page endpoint
- `app.py`: Scheduler configuration

## Debugging Checklist

When automation isn't working:

1. **Check scheduler**: Verify jobs are running in logs
2. **Check database**: Query for bets with `api_fetched='No'`
3. **Check Issues page**: Look for logged errors
4. **Check ESPN API**: Verify game data availability
5. **Check player data**: Ensure players exist in database
6. **Check dates**: Verify game dates are correct
7. **Check logs**: Look for specific error messages

## Manual Testing

To test the automation manually:

```python
from automation.historical_bet_processing import process_historical_bets_api
process_historical_bets_api()
```

To check bet status:

```python
from app import app, db
from models import Bet

with app.app_context():
    bet = Bet.query.get(bet_id)
    print(f"Status: {bet.api_fetched}, Active: {bet.is_active}")
```