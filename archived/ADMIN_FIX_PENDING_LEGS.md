# Admin Tool: Fix Pending Bet Legs

## Overview
A new admin endpoint and UI to manually fix all pending bet legs by querying the ESPN API.

## Problem Solved
Sometimes bet legs remain in 'pending' status even after games have finished. This can happen due to:
- Games finishing when the automation wasn't running
- API errors during automated updates
- Missing data (game_id, achieved_value, etc.)
- Manual bet entry without complete data

## Solution
The `/admin/fix_pending_legs` endpoint provides a manual "fix-all" button that:

1. **Finds all pending legs** - Queries database for `BetLeg` records with `status='pending'`
2. **Fetches ESPN data** - For each leg, calls `fetch_game_details_from_espn()` with game date and teams
3. **Updates missing data**:
   - **game_id** (ESPN game ID) if missing
   - **achieved_value** if blank (uses `calculate_bet_value()` function)
   - **status** ('won' or 'lost') based on achieved vs target
   - **is_hit** (True/False) based on status

## Features

### Admin Endpoint
**Route:** `POST /admin/fix_pending_legs`  
**Auth:** Requires `@login_required`  
**Returns:** JSON with stats and details

```json
{
  "success": true,
  "message": "Fixed 15 out of 20 pending legs",
  "stats": {
    "total_pending": 20,
    "fixed": 15,
    "skipped": 3,
    "errors": 2,
    "game_id_added": 12,
    "achieved_value_added": 15,
    "status_updated": 15
  },
  "details": [
    {
      "leg_id": 123,
      "bet_id": 45,
      "player": "Patrick Mahomes",
      "game": "KC @ BUF",
      "game_date": "2025-11-10",
      "changes": [
        "Added game_id: 401547634",
        "Added achieved_value: 275.0",
        "Updated status: won, is_hit: True"
      ]
    }
  ]
}
```

### Admin UI
**Route:** `GET /admin.html`  
**Auth:** Requires `@login_required`

Clean, modern UI with:
- **One-click fix button** - "🚀 Fix All Pending Legs"
- **Real-time stats** - Total pending, fixed, skipped, errors
- **Detailed changelog** - Shows exactly what changed for each leg
- **Additional tools** - Compute Returns, Update Teams

## How It Works

### 1. Query Database
```python
pending_legs = BetLeg.query.filter_by(status='pending').all()
```

### 2. Fetch ESPN Data
```python
game_data = fetch_game_details_from_espn(
    game_date=leg.game_date.strftime('%Y-%m-%d'),
    away_team=leg.away_team,
    home_team=leg.home_team,
    sport=leg.sport or 'NFL'
)
```

### 3. Extract Stats
Uses existing `calculate_bet_value()` function:
```python
bet_dict = {
    'player': leg.player_name,
    'team': leg.player_team or leg.home_team,
    'stat': leg.stat_type or '',
    'target': leg.target_value,
    'game_date': game_date_str,
    'away': leg.away_team,
    'home': leg.home_team
}
achieved = calculate_bet_value(bet_dict, game_data)
```

### 4. Calculate Status
```python
if stat_type == 'moneyline':
    leg_status = 'won' if leg.achieved_value > 0 else 'lost'
elif stat_type == 'spread':
    leg_status = 'won' if (leg.achieved_value + leg.target_value) > 0 else 'lost'
else:  # Player props
    if leg.bet_line_type == 'under':
        leg_status = 'won' if leg.achieved_value < leg.target_value else 'lost'
    else:
        leg_status = 'won' if leg.achieved_value >= leg.target_value else 'lost'

leg.status = leg_status
leg.is_hit = True if leg_status == 'won' else False
```

### 5. Commit Changes
```python
db.session.commit()
```

## Use Cases

### Scenario 1: Automation Missed Games
- User: "Some of my legs are still pending even though games finished"
- Solution: Navigate to `/admin.html`, click "Fix All Pending Legs"
- Result: All completed games get their final stats and status updated

### Scenario 2: Manual Entry Missing Data
- User: Manually entered bet but left some fields blank
- Solution: Run fix tool after games complete
- Result: ESPN data fills in game_id, achieved_value, status

### Scenario 3: API Errors
- Automation failed due to rate limits or network issues
- Solution: Run manual fix during off-peak hours
- Result: Catches up on all missed updates

### Scenario 4: Historical Data
- Imported old bets from JSON/CSV with status='pending'
- Solution: Run fix tool to retroactively calculate outcomes
- Result: All historical legs get proper won/lost status

## Safety Features

### Skip Conditions
The tool will **skip** legs that:
- Missing `game_date`, `away_team`, or `home_team`
- Game not found on ESPN (too old, different league)
- Already have `status='won'` or `status='lost'` AND `is_hit` is set

### Protection
- **Only updates pending legs** - Won't overwrite already-determined results
- **Respects is_hit column** - If `is_hit` is already True/False, skips the leg
- **Transaction safety** - Uses `db.session.commit()` with rollback on errors
- **Detailed logging** - Every change is logged for audit trail

### Error Handling
```python
try:
    # Process leg
    leg.status = leg_status
    leg.is_hit = is_hit_value
except Exception as e:
    app.logger.error(f"[MANUAL FIX] Error processing leg {leg.id}: {e}")
    stats['errors'] += 1
    continue  # Continue with next leg
```

## Stats Breakdown

| Stat | Description |
|------|-------------|
| **total_pending** | Number of legs found with status='pending' |
| **fixed** | Legs successfully updated with new data |
| **skipped** | Legs skipped (missing data, game not found) |
| **errors** | Legs that threw errors during processing |
| **game_id_added** | Count of legs that got ESPN game_id |
| **achieved_value_added** | Count of legs that got final stat value |
| **status_updated** | Count of legs that got won/lost status |

## Comparison with Automation

| Feature | Automation (`update_completed_bet_legs`) | Manual Fix (`admin_fix_pending_legs`) |
|---------|------------------------------------------|---------------------------------------|
| **Trigger** | Background job (every 5 minutes) | Manual button click |
| **Scope** | Only bets with `status='completed'` | ALL legs with `status='pending'` |
| **Use Case** | Continuous monitoring | One-time catch-up |
| **Speed** | Runs automatically | On-demand, faster |
| **Visibility** | Logs only | Full UI with stats |

## Files Modified

1. **app.py**
   - Added `@app.route('/admin/fix_pending_legs')` endpoint (line ~2118)
   - Added `@app.route('/admin.html')` route (line ~3073)
   - Uses existing `fetch_game_details_from_espn()` and `calculate_bet_value()` functions

2. **admin.html** (NEW)
   - Clean, modern admin UI
   - Real-time stats display
   - Detailed changelog
   - Multiple admin tools in one page

## Usage

### Access Admin Page
```
http://localhost:5001/admin.html
```

### API Call (Programmatic)
```bash
curl -X POST http://localhost:5001/admin/fix_pending_legs \
  -H "Content-Type: application/json" \
  -b cookies.txt
```

### From Python
```python
import requests

response = requests.post(
    'http://localhost:5001/admin/fix_pending_legs',
    cookies={'session': 'your-session-cookie'}
)
data = response.json()
print(f"Fixed {data['stats']['fixed']} legs")
```

## Logging

All operations are logged with `[MANUAL FIX]` prefix:

```
[MANUAL FIX] Starting manual fix for all pending legs...
[MANUAL FIX] Found 20 pending legs
[MANUAL FIX] Leg 123: Fetching NFL game KC @ BUF on 2025-11-10
[MANUAL FIX] Leg 123: Added game_id 401547634
[MANUAL FIX] Leg 123: Added achieved_value 275.0
[MANUAL FIX] Leg 123: Updated status=won, is_hit=True
[MANUAL FIX] Complete: Fixed 15/20 legs
```

## Future Enhancements

Potential improvements:
- **Selective fix** - Fix only specific bet IDs or date ranges
- **Dry run mode** - Preview changes before committing
- **Scheduling** - Auto-run fix at specific times
- **Notifications** - Email/SMS when fix completes
- **Undo function** - Revert changes if needed
- **Batch processing** - Process in chunks for large datasets

## Testing Checklist

- [ ] Create test bet with pending legs
- [ ] Verify games have finished on ESPN
- [ ] Navigate to `/admin.html`
- [ ] Click "Fix All Pending Legs"
- [ ] Verify stats show correct counts
- [ ] Check details list for changes
- [ ] Confirm database updated (status, is_hit, achieved_value)
- [ ] Verify logs show all operations
- [ ] Test with missing data (should skip gracefully)
- [ ] Test with already-determined legs (should skip)
- [ ] Test error handling (invalid game dates, etc.)

## Troubleshooting

### "No pending legs found"
- All legs already have status='won' or 'lost'
- Check database: `SELECT * FROM bet_legs WHERE status='pending'`

### "Skipped - game not found on ESPN"
- Game too old (ESPN only keeps recent games)
- Team names don't match ESPN format
- Wrong sport code
- Game hasn't happened yet

### "Skipped - missing game_date or teams"
- Leg created with incomplete data
- Manually update: `UPDATE bet_legs SET game_date=... WHERE id=...`

### High error count
- ESPN API rate limiting (wait a few minutes)
- Network issues (check internet connection)
- Invalid data in database (check logs for specific errors)

---

**Created:** November 12, 2025  
**Author:** AI Assistant  
**Version:** 1.0
