# Automation Package

This package contains all automated background tasks for the Parlay Tracker application.

## Overview

The automations are organized into separate modules for better maintainability and testing. Each automation runs on a scheduled basis using APScheduler.

## Automations

### 1. Live Bet Updates (`live_bet_updates.py`)
- **Frequency**: Every 1 minute
- **Purpose**: Updates live/pending bets with real-time ESPN data
- **What it does**:
  - Fetches current scores and game status from ESPN API
  - Updates `achieved_value`, `game_status`, `home_score`, `away_score`, and `game_id` for active bets
  - Keeps live bets showing real-time data during games

### 2. Completed Bet Updates (`completed_bet_updates.py`)
- **Frequency**: Every 30 minutes
- **Purpose**: Automatically populates final results for completed bets when games finish
- **What it does**:
  - Finds bets with `status='completed'` that have legs with `game_status='STATUS_FINAL'`
  - Fetches final game data from ESPN API
  - Updates `achieved_value`, `status` (won/lost), `game_status`, and scores
  - Uses same logic as manual `/historical` endpoint

### 3. Team Name Standardization (`team_name_standardization.py`)
- **Frequency**: Every 24 hours
- **Purpose**: Ensures consistent team names across the database
- **What it does**:
  - Maps team names to standardized `team_name_short` values from the teams table
  - Updates bet legs with correct team names
  - Handles both NFL and NBA teams

### 4. Bet Status Management (`bet_status_management.py`)
Contains two related automations:

#### Auto-Move Bets with No Live Legs
- **Frequency**: Every 5 minutes
- **Purpose**: Moves bets from live to historical when all games are finished
- **What it does**:
  - Checks live bets where no legs have games in progress (`STATUS_IN_PROGRESS` or `STATUS_HALFTIME`)
  - Sets `is_active=False`, `status='completed'`, `api_fetched='Yes'`

#### Auto-Determine Leg Hit Status
- **Frequency**: Every 10 minutes
- **Purpose**: Determines hit/miss status for bet legs with final results
- **What it does**:
  - Finds legs with `achieved_value` but no `is_hit` status where `game_status='STATUS_FINAL'`
  - Calculates won/lost based on bet type (moneyline, spread, player props)
  - Updates `is_hit` and `status` fields

## Usage

### Running Individual Automations

You can run any automation script standalone for testing:

```bash
# Test live bet updates
python automation/live_bet_updates.py

# Test completed bet updates
python automation/completed_bet_updates.py

# Test team name standardization
python automation/team_name_standardization.py

# Test bet status management (both functions)
python automation/bet_status_management.py

# Test only auto-move functionality
python automation/bet_status_management.py move_bets

# Test only hit status determination
python automation/bet_status_management.py hit_status
```

### Scheduling

All automations are automatically scheduled when the Flask app starts via APScheduler in `app.py`. The scheduler configuration is in the bottom of `app.py`.

## Architecture Benefits

1. **Separation of Concerns**: Main app focuses on web routes, automations are isolated
2. **Maintainability**: Easier to modify automations without touching main application
3. **Testing**: Can test automations independently
4. **Scalability**: Can potentially run automations on separate workers/processes
5. **Code Organization**: Related functionality grouped together

## Dependencies

- APScheduler (for scheduling)
- Flask app context (for database access)
- ESPN API access (for live data)
- Database models and helpers

## Logging

All automations use structured logging with prefixes:
- `[LIVE-UPDATE]`: Live bet updates
- `[AUTO-UPDATE]`: Completed bet updates
- `[TEAM-STANDARDIZE]`: Team name standardization
- `[AUTO-MOVE-NO-LIVE]`: Bet status management (move bets)
- `[AUTO-HIT-STATUS]`: Bet status management (hit status)