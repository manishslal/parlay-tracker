# Automated Bet Leg Updates

## Overview

An automated background process that updates bet legs with final game results when their status becomes `STATUS_FINAL`.

## How It Works

### The Problem
Previously, bet legs would only get their final `achieved_value` and `status` (won/lost) updated when a user explicitly requested the `/historical` endpoint. This meant:
- Completed bets might sit without final results for hours/days
- Data was only updated on-demand, not automatically
- Historical views would show incomplete information until manually triggered

### The Solution
A background scheduler (APScheduler) runs every 5 minutes to:

1. **Find** all bets with `status='completed'` in the database
2. **Check** each bet's legs for:
   - Legs where `game_status='STATUS_FINAL'`
   - Missing `achieved_value` OR `status='pending'`
3. **Fetch** fresh game data from ESPN API for those bets
4. **Update** the `bet_legs` table with:
   - `achieved_value` - Final stat value (points scored, score differential, etc.)
   - `status` - Won or lost based on bet type logic
   - `game_status` - Updated to `STATUS_FINAL`
   - `home_score` and `away_score` - Final scores

### Trigger Condition
The automation specifically activates when:
- A bet has `status='completed'` (meaning the user marked it as finished)
- One or more legs have `game_status='STATUS_FINAL'` **for the first time**
- Those legs are still missing final data (`achieved_value=NULL` or `status='pending'`)

## Implementation Details

### Components Added

#### 1. Background Scheduler Setup (`app.py` lines 6-11, 177-182)
```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit

# Setup background scheduler for automated tasks
scheduler = BackgroundScheduler()
scheduler.start()

# Shut down scheduler on app exit
atexit.register(lambda: scheduler.shutdown())
```

#### 2. Automation Function (`app.py` after line 517)
```python
def update_completed_bet_legs():
    """Background job to automatically update bet legs when games become final."""
    # ... (see code for full implementation)
```

Key features:
- Finds all completed bets
- Calls `to_dict_structured(use_live_data=True)` to fetch fresh ESPN data
- Updates only legs that need updating (game is final but no achieved_value)
- Calculates won/lost status based on bet type:
  - **Moneyline**: Won if score_diff > 0
  - **Spread**: Won if (score_diff + spread) > 0
  - **Player Props**: Won if achieved >= target (or < for unders)
- Commits all updates in a single transaction
- Logs detailed information about what was updated

#### 3. Scheduled Job Registration (`app.py` in `if __name__ == "__main__"`)
```python
# Schedule automated bet leg updates every 5 minutes
def run_scheduled_update():
    with app.app_context():
        update_completed_bet_legs()

scheduler.add_job(
    func=run_scheduled_update,
    trigger=IntervalTrigger(minutes=5),
    id='update_bet_legs',
    name='Update completed bet legs with final results',
    replace_existing=True
)
```

### Dependencies
- **APScheduler 3.10.4** - Added to `requirements.txt`
- Background scheduler runs independently of Flask request handlers
- Uses Flask app context for database access

## Testing

### Test Script
Created `test_automation.py` to verify functionality:

```bash
python test_automation.py
```

Results:
- ✓ Successfully finds completed bets (110 found in test)
- ✓ Processes legs with final game status
- ✓ Updates achieved_value and status correctly
- ✓ Handles errors gracefully (e.g., no internet connection)

### Manual Testing
```python
# In Python console with app context
from app import app, update_completed_bet_legs

with app.app_context():
    update_completed_bet_legs()
```

## Logs

The automation produces detailed logs:

```
[AUTO-UPDATE] Starting bet leg update check...
[AUTO-UPDATE] Checking 110 completed bets
[AUTO-UPDATE] Bet 106 Leg 1: achieved_value = -17.0
[AUTO-UPDATE] Bet 106 Leg 1: status = lost
[AUTO-UPDATE] Bet 106 Leg 2: achieved_value = 22.0
[AUTO-UPDATE] Bet 106 Leg 2: status = won
[AUTO-UPDATE] ✓ Updated 2 legs across 1 bets
```

## Production Deployment

### Render.com
When deployed to Render:
1. APScheduler is automatically installed via `requirements.txt`
2. Scheduler starts when the Gunicorn worker starts
3. Runs every 5 minutes in the background
4. Survives across requests (persistent background thread)

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the app (scheduler starts automatically)
python app.py
```

## Benefits

1. **Automated Data Completeness**
   - No manual intervention needed for historical bets
   - Data stays up-to-date automatically

2. **Accurate Historical Views**
   - Historical bets show correct won/lost status immediately
   - `achieved_value` populated for all completed games

3. **Performance Improvement**
   - Spreads ESPN API load over time (every 5 minutes)
   - `/historical` endpoint no longer needs to fetch live data
   - Faster page loads for users viewing historical bets

4. **Data Reliability**
   - Single source of truth in `bet_legs` table
   - Consistent calculation logic (same as `/historical` endpoint)
   - Handles edge cases (no internet, missing games, etc.)

## Future Enhancements

Possible improvements:
- Make interval configurable via environment variable
- Add separate job for "live" bets (more frequent checks)
- Send notifications when all legs of a parlay become final
- Archive old completed bets to separate table
- Add metrics/monitoring for automation success rate

## Troubleshooting

### Scheduler Not Running
Check logs for: `✓ Scheduled automated bet leg updates (every 5 minutes)`

### Updates Not Happening
1. Verify bets have `status='completed'`
2. Check legs have `game_status='STATUS_FINAL'`
3. Look for `[AUTO-UPDATE]` logs
4. Verify ESPN API is accessible

### High Memory Usage
- Scheduler is lightweight (BackgroundScheduler)
- Consider reducing interval if processing many bets
- Limit batch size in `update_completed_bet_legs()` if needed
