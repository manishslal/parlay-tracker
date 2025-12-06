# ROOT CAUSE ANALYSIS & COMPREHENSIVE SOLUTION
## Bet 204 Data Flow Failure

Generated: 2025-12-06
Status: CRITICAL - Multiple System Failures

---

## EXECUTIVE SUMMARY

Bet 204 failed to process correctly due to **4 cascading failures**:
1. ✅ **Scheduler Downtime** (14+ hours)
2. ✅ **"TBD" Pollution** (should be NULL)
3. ✅ **Incomplete Automation** (only checks `status='live'`)
4. ✅ **Wrong Status Logic** (should be 'lost', not 'completed')

---

## DETAILED ROOT CAUSE ANALYSIS

### 1. SCHEDULER DOWNTIME (PRIMARY CAUSE)

**Timeline:**
```
11:39 PM (12/5): Bet 204 created via OCR
11:39 PM - 2:13 PM (12/6): SCHEDULER NOT RUNNING (14+ hours!)
2:13 PM (12/6): Scheduler starts (after deployment)
2:14 PM: Automations run but games already finished
```

**Impact:**
- Games finished before `populate_missing_game_ids` could run
- Bet never transitioned from `pending` → `live` → `completed`
- 6 legs stuck with `TBD` teams and no `game_id`

**Root Cause:**
- Render deploys don't automatically restart background scheduler
- Scheduler only starts when app.py loads
- Previous deployment crashed or didn't include scheduler

---

### 2. "TBD" STRING POLLUTION

**Source:** `routes/bets.py` lines 893, 906

```python
# OCR bet creation
away_team = 'TBD'  # Will be resolved by game matching
```

**Why This Is Bad:**
1. Database has `away_team = 'TBD'` instead of `NULL`
2. Team matching logic checks `if leg.away_team == 'TBD'` (string comparison)
3. Should use `IS NULL` in SQL for better query performance
4. "TBD" is a magic string - harder to debug

**Current Flow:**
```
OCR → away_team='TBD' → populate_missing_game_ids → should update to real team
```

**Failure Point:**
If scheduler doesn't run before games finish, teams stay as 'TBD' forever!

---

### 3. INCOMPLETE AUTOMATION COVERAGE

**Problem:** `auto_move_bets_no_live_legs` ONLY checks `status='live'`

`automation/bet_status_management.py` line 32:
```python
live_bets = Bet.query.filter(
    Bet.status == 'live',  # ← MISSES pending bets!
    Bet.is_active == True,
    ...
).all()
```

**Impact:**
- Bet 204 has `status='pending'`
- Automation skips it completely
- Bet stuck in limbo forever
- Shows in "Live Bets" UI but shouldn't

**Missing Cases:**
1. Pending bets with completed games (like Bet 204)
2. Pending bets that never became live due to scheduler downtime
3. Bets created minutes before games start

---

### 4. WRONG STATUS LOGIC

`automation/bet_status_management.py` lines 118-122:
```python
new_status = 'completed' # Default fallback
if all_legs_won:
    new_status = 'won'
elif any_leg_lost:
    new_status = 'lost'  # ← Should use this!
```

**Problem:**
- Bet.status set to 'completed' when all legs won OR any lost
- User wants 'lost' for any losing leg
- 'completed' should only be for pending/void cases

**Impact:**
- Lost bets marked as 'completed' instead of 'lost'
- Harder to filter/report on performance
- UI shows wrong status

---

## BET 204 SPECIFIC FINDINGS

### Data State:
```
Bet ID: 204
Status: pending (WRONG - should be 'lost')
Is Active: True (WRONG - should be False)
Created: 2025-12-05 23:39:23
Game Date: 2025-12-05

LEGS:
- 4 legs: NULL teams, game_id=401810193, STATUS_FINAL, have achieved values
  → PARTIAL SUCCESS (game matched, stats fetched)
  
- 6 legs: TBD teams, no game_id, STATUS_SCHEDULED, no achieved values
  → TOTAL FAILURE (never processed)

RESULTS:
- 3 legs WON
- 1 leg LOST (Deandre Ayton pts: 6/10)
- 6 legs PENDING (stuck)
```

### Why Partial Success?

**Legs 1-4** (NULL teams):
- Created at 11:39 PM
- First update at 11:42 PM (2min later) - `populate_missing_player_data` ran!
- Got game_id=401810193
- Scheduler was still running briefly
- Got team names cleared (NULL instead of staying TBD somehow)
- Updates at 2:26 AM and 2:29 AM - `live_bet_updates` ran!
  
**Legs 5-10** (TBD teams):
- Created at 11:39 PM
- Last update at 11:42 PM (2min later) - set to TBD
- Never updated again
- Scheduler stopped after that
- Games finished while scheduler was down

---

## PROPOSED SOLUTION

### SHORT-TERM FIXES (Deploy Immediately)

#### Fix 1: Use NULL instead of "TBD"
**File:** `routes/bets.py` lines 893, 902, 906

```python
# BEFORE:
away_team = 'TBD'  # Will be resolved by game matching

# AFTER:
away_team = None  # Will be resolved by game matching
```

**Rationale:**
- NULL is semantically correct for "unknown"
- Better for SQL queries (`IS NULL` vs `= 'TBD'`)
- No magic strings

---

#### Fix 2: Update auto_move to check pending bets too
**File:** `automation/bet_status_management.py` lines 32-36

```python
# BEFORE:
live_bets = Bet.query.filter(
    Bet.status == 'live',
    Bet.is_active == True,
    ...
).all()

# AFTER:
live_bets = Bet.query.filter(
    Bet.status.in_(['live', 'pending']),  # ← Check both!
    Bet.is_active == True,
    Bet.status.notin_(['won', 'lost', 'completed'])
).all()
```

**Rationale:**
- Catches bets that never transitioned to live
- Handles scheduler downtime gracefully
- Prevents bets from being stuck forever

---

#### Fix 3: Change status to 'lost' instead of 'completed'
**File:** `automation/bet_status_management.py` line 118

```python
# BEFORE:
new_status = 'completed' # Default fallback
if all_legs_won:
    new_status = 'won'
elif any_leg_lost:
    new_status = 'lost'

# AFTER:
if all_legs_won:
    new_status = 'won'
elif any_leg_lost:
    new_status = 'lost'  # ← Use this for any loss!
else:
    new_status = 'completed'  # Only for void/push cases
```

**Rationale:**
- Clear distinction: won/lost/completed (push/void)
- Better for analytics and filtering
- Matches user expectations

---

#### Fix 4: Check game_id population logic
**File:** `app.py` line 537

```python
# CURRENT:
leg_needs_update = (not leg.game_id or leg.game_id == '') or (not leg.away_team or leg.away_team == 'TBD')

# UPDATE TO:
leg_needs_update = (
    (not leg.game_id or leg.game_id == '') or 
    (leg.away_team is None or leg.away_team == 'TBD' or leg.away_team == '')
)
```

**Rationale:**
- Handles NULL, 'TBD', and empty string cases
- More robust
- Catches all incomplete data

---

### MEDIUM-TERM FIXES (Next Sprint)

#### Fix 5: Ensure scheduler resilience

**Add health check:**
```python
# app.py
@app.route('/health/scheduler')
def scheduler_health():
    return jsonify({
        'running': scheduler.running,
        'jobs': len(scheduler.get_jobs()),
        'next_run': str(scheduler.get_jobs()[0].next_run_time) if scheduler.get_jobs() else None
    })
```

**Add startup diagnostics:**
```python
# Log all jobs on startup
for job in scheduler.get_jobs():
    logger.info(f"Scheduled job: {job.id} - next run: {job.next_run_time}")
```

---

#### Fix 6: Add fallback for missed automations

**Create recovery job:**
```python
def recover_stuck_bets():
    """Find and fix bets that slipped through automation cracks"""
    # Find pending/live bets with old dates
    stuck_bets = Bet.query.filter(
        Bet.status.in_(['pending', 'live']),
        Bet.is_active == True,
        Bet.bet_date < (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    ).all()
    
    for bet in stuck_bets:
        logger.warning(f"STUCK BET FOUND: {bet.id} - status={bet.status}, date={bet.bet_date}")
        # Process with ESPN API
        process_stuck_bet(bet)

# Run daily at 4 AM
scheduler.add_job(
    func=recover_stuck_bets,
    trigger=CronTrigger(hour=4, minute=0),
    id='recover_stuck_bets',
    name='Find and fix stuck bets daily'
)
```

---

## IMMEDIATE ACTIONS

### 1. Fix Bet 204 Manually

```sql
-- Set correct status
UPDATE bets 
SET status = 'lost', 
    is_active = FALSE
WHERE id = 204;

-- Mark all legs as final
UPDATE bet_legs
SET game_status = 'STATUS_FINAL'
WHERE bet_id = 204;
```

### 2. Find Other Stuck Bets

```sql
-- Find all bets like 204
SELECT b.id, b.status, b.is_active, b.bet_date,
       COUNT(bl.id) as num_legs,
       COUNT(CASE WHEN bl.game_status = 'STATUS_FINAL' THEN 1 END) as final_legs
FROM bets b
JOIN bet_legs bl ON bl.bet_id = b.id
WHERE b.status = 'pending'
  AND b.is_active = TRUE
  AND bl.game_date < CURRENT_DATE
GROUP BY b.id
HAVING COUNT(CASE WHEN bl.game_status = 'STATUS_FINAL' THEN 1 END) > 0;
```

### 3. Deploy Fixes

Priority order:
1. ✅ Fix 2 (check pending bets) - CRITICAL
2. ✅ Fix 3 (lost vs completed) - HIGH
3. ✅ Fix 1 (NULL instead of TBD) - MEDIUM
4. ✅ Fix 4 (game_id logic) - LOW

---

## SUCCESS METRICS

After deployment, verify:
- [ ] No bets with status='pending' and game_date < yesterday
- [ ] No bets with away_team='TBD' and game_status='STATUS_FINAL'
- [ ] All lost bets have status='lost', not 'completed'
- [ ] Scheduler health endpoint returns 200
- [ ] Background jobs show in Render logs every minute/hour

---

## LESSONS LEARNED

1. **Always check for NULL AND magic strings** ('TBD', 'Unknown', etc.)
2. **Automations must handle edge cases** (scheduler downtime, late creation)
3. **Status transitions need all paths** (pending → live, pending → completed)
4. **Recovery jobs are essential** - automations will miss things!
5. **Health checks prevent silent failures**

---

## TIMELINE FOR IMPLEMENTATION

**Today (Critical):**
- Deploy Fix 2 (check pending bets)
- Deploy Fix 3 (lost status)
- Manually fix Bet 204

**This Week:**
- Deploy Fix 1 (NULL instead of TBD)
- Add scheduler health check
- Audit all stuck bets

**Next Week:**
- Deploy Fix 6 (recovery job)
- Add monitoring/alerts
- Document runbook for stuck bets
