# Data Validation Automation

## Overview

Daily automation that validates historical bet data against ESPN API and reports discrepancies for manual review.

## Schedule
**Frequency**: Every 24 hours  
**Job ID**: `validate_historical_data`

## What It Checks

### 1. **Achieved Value Validation**
Compares `bet_legs.achieved_value` (stored in database) with live ESPN API data.

**Reports**:
- Bet ID
- Leg ID
- Player name
- Stat type
- Stored value vs ESPN value
- Difference
- Game details (teams, date)

### 2. **Game ID Validation**
Verifies that `bet_legs.game_id` correctly links to ESPN game.

**Checks**:
- Game ID matches ESPN's game for those teams/date
- Teams and date match the game

**Reports**:
- Stored game_id vs ESPN game_id
- Mismatch details

### 3. **Missing Game IDs**
Identifies legs without `game_id` and attempts to find the correct ESPN game.

**Reports**:
- Legs without game_id
- Whether matching ESPN game was found
- Suggested ESPN game_id if found

## Sample Output

### No Issues (Clean)
```
[DATA-VALIDATION] ===== VALIDATION REPORT =====
[DATA-VALIDATION] Total legs validated: 3
[DATA-VALIDATION] Value mismatches: 0
[DATA-VALIDATION] Game ID issues: 0
[DATA-VALIDATION] Missing game IDs: 0
[DATA-VALIDATION] Validation errors: 0
[DATA-VALIDATION] ===== END VALIDATION REPORT =====
```

### With Issues
```
[DATA-VALIDATION] ===== VALUE MISMATCHES =====
[DATA-VALIDATION] MISMATCH | Bet 6 Leg 23 | Donovan Mitchell points | 
    DB: 0.00 vs ESPN: 17.00 (diff: 17.00) | Cleveland Cavaliers @ Toronto Raptors | 2025-11-24

[DATA-VALIDATION] ===== GAME ID ISSUES =====
[DATA-VALIDATION] GAME_ID_ISSUE | Bet 8 Leg 45 | Stephen Curry | 
    Utah Jazz @ Golden State Warriors | Issue: game_id mismatch

[DATA-VALIDATION] ===== MISSING GAME IDS =====
[DATA-VALIDATION] NO_GAME_ID | Bet 12 Leg 67 | Darius Garland assists | 
    Cleveland Cavaliers @ Toronto Raptors | ESPN ID: 401810139 | Game found on ESPN but not linked
```

## How to Use

### Run Manually (Testing)
```bash
docker-compose exec web python automation/data_validation.py
```

### Check Logs
```bash
docker-compose logs web | grep "DATA-VALIDATION"
```

### Review Report
The validation report appears in application logs daily. Look for:
- `[DATA-VALIDATION] MISMATCH` - Value doesn't match ESPN
- `[DATA-VALIDATION] GAME_ID_ISSUE` - Game ID linking problem
- `[DATA-VALIDATION] NO_GAME_ID` - Missing game ID

## What to Do with Issues

### Value Mismatch
1. **Verify ESPN is correct**: Check ESPN website manually
2. **Update database**: If ESPN is correct, update `achieved_value`:
   ```sql
   UPDATE bet_legs SET achieved_value = <correct_value> WHERE id = <leg_id>;
   ```
3. **Or run manual update script** if value was 0 due to the bug we fixed

### Game ID Issue
1. **Check the suggested ESPN game_id** from the report
2. **Update if mismatch**:
   ```sql
   UPDATE bet_legs SET game_id = '<correct_game_id>' WHERE id = <leg_id>;
   ```

### Missing Game ID
1. **If ESPN ID found in report**, link it:
   ```sql
   UPDATE bet_legs SET game_id = '<espn_game_id>' WHERE id = <leg_id>;
   ```
2. **If not found**, game may not exist on ESPN (future game, cancelled, etc.)

## Benefits

✅ **Catches data corruption** from API glitches or bugs  
✅ **Identifies linking issues** before they affect analytics  
✅ **Provides audit trail** of data quality  
✅ **Runs automatically** - no manual checking needed  
✅ **Non-invasive** - only reports, doesn't auto-fix (prevents accidental overwrites)

## Advanced: Filtering the Report

To see only specific bet issues:
```bash
# Only value mismatches
docker-compose logs web | grep "MISMATCH"

# Only game ID issues
docker-compose logs web | grep "GAME_ID_ISSUE"

# Only missing game IDs
docker-compose logs web | grep "NO_GAME_ID"

# Specific bet
docker-compose logs web | grep "DATA-VALIDATION.*Bet 6"
```

## Future Enhancements

Potential improvements:
- [ ] Email/Slack alerts for critical mismatches
- [ ] Auto-fix minor mismatches (with confirmation)
- [ ] Track mismatch trends over time
- [ ] Check player stats (season avg, etc.) if populated
- [ ] Validate bet-level data (odds, returns, etc.)
