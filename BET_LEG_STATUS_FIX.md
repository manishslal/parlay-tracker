# Bet Leg Status Protection Fix

## Problem
Bet legs that already had `status='won'` or `status='lost'` were being changed back to `'pending'` by the automation system.

## Root Cause
The `is_hit` column was not being set when legs were created or when status was calculated. This caused the automation to treat legs with determined results as "incomplete" and recalculate them.

### Specific Issues:

1. **save_bet_to_db() (line ~249)**
   - Created legs with `status='won'` or `status='lost'` but left `is_hit=None`
   - Automation saw `is_hit=None` and assumed leg needed recalculation

2. **update_bet_from_espn() (line ~662)**
   - Set `status` but didn't set `is_hit`
   - Didn't check if `is_hit` was already set before updating

3. **save_final_results_to_db() (line ~382)**
   - Set `status` but didn't set `is_hit`

4. **update_bet_results_from_espn() (line ~887)**
   - Checked: `if leg.status == 'pending' or leg.is_hit is None:`
   - This meant legs with `status='won'` but `is_hit=None` would be recalculated!

## Solution

### 1. Save `is_hit` When Creating Legs
**File:** `app.py` - `save_bet_to_db()` function

```python
# Set is_hit based on status (prevents automation from overwriting)
if leg_status == 'won':
    bet_leg.is_hit = True
elif leg_status == 'lost':
    bet_leg.is_hit = False
# Leave as None for 'pending' status
```

**Why:** When creating a leg with a known outcome, immediately set `is_hit` so automation knows not to recalculate.

---

### 2. Set `is_hit` in save_final_results_to_db()
**File:** `app.py` - `save_final_results_to_db()` function (line ~382)

```python
bet_leg.status = leg_status
bet_leg.is_hit = True if leg_status == 'won' else False  # ✅ ADDED
updated = True
```

**Why:** When manually saving final results, mark the leg as determined so automation respects it.

---

### 3. Set `is_hit` in update_bet_from_espn()
**File:** `app.py` - `update_bet_from_espn()` function (line ~662)

**Before:**
```python
if bet_leg.status == 'pending' and bet_leg.achieved_value is not None:
    # ... calculate leg_status ...
    bet_leg.status = leg_status
    leg_updated = True
```

**After:**
```python
# Only update if status is pending AND is_hit is None (not already determined)
if bet_leg.status == 'pending' and bet_leg.is_hit is None and bet_leg.achieved_value is not None:
    # ... calculate leg_status ...
    bet_leg.status = leg_status
    bet_leg.is_hit = True if leg_status == 'won' else False  # ✅ ADDED
    leg_updated = True
```

**Why:** 
- Added `is_hit is None` check to prevent overwriting already-determined results
- Set `is_hit` when calculating status for the first time

---

### 4. Stricter Check in update_bet_results_from_espn()
**File:** `app.py` - `update_bet_results_from_espn()` function (line ~887)

**Before:**
```python
# This was the PROBLEM - used OR instead of AND
if leg.status == 'pending' or leg.is_hit is None:
```

**After:**
```python
# CRITICAL: Only update if BOTH status is pending AND is_hit is None
# This prevents overwriting manually set or previously calculated results
if leg.status == 'pending' and leg.is_hit is None:
```

**Why:** 
- Changed from `OR` to `AND` - BOTH conditions must be true
- A leg with `status='won'` but `is_hit=None` will NOT be recalculated
- A leg with `status='pending'` but `is_hit=True` will NOT be recalculated
- Only truly undetermined legs (`status='pending'` AND `is_hit=None`) will be updated

---

## Testing

### Test Case 1: New Leg Created with Status
```python
# When creating a leg with status='won'
leg_data = {'status': 'won', 'player': 'LeBron James', ...}
save_bet_to_db(user_id, bet_data)

# Expected Result:
# bet_leg.status = 'won'
# bet_leg.is_hit = True  ✅ Now set!
```

### Test Case 2: Automation Respects Determined Legs
```python
# Existing leg: status='won', is_hit=True
# Automation runs update_bet_results_from_espn()

# Check: leg.status == 'pending' and leg.is_hit is None
# Result: FALSE (status is 'won', not 'pending')
# Action: SKIP - leg is not updated ✅
```

### Test Case 3: Automation Updates Truly Pending Legs
```python
# Existing leg: status='pending', is_hit=None
# Game finishes, achieved_value is populated
# Automation runs update_bet_from_espn()

# Check: status == 'pending' and is_hit is None and achieved_value is not None
# Result: TRUE
# Action: Calculate status, set is_hit ✅
```

---

## Database State

### Column: `is_hit`
| Value | Meaning | When Set |
|-------|---------|----------|
| `None` | Undetermined - leg result not calculated yet | Default for `status='pending'` |
| `True` | Leg won | When `status='won'` |
| `False` | Leg lost | When `status='lost'` |

### Valid States
| status | is_hit | Valid? | Meaning |
|--------|--------|--------|---------|
| `'pending'` | `None` | ✅ Yes | Game hasn't finished, result unknown |
| `'pending'` | `True/False` | ⚠️ Rare | Manually set before game ends |
| `'won'` | `True` | ✅ Yes | Leg won |
| `'won'` | `None` | ❌ Bug | **OLD BUG** - would be recalculated |
| `'lost'` | `False` | ✅ Yes | Leg lost |
| `'lost'` | `None` | ❌ Bug | **OLD BUG** - would be recalculated |

---

## Protection Logic Summary

### Before Fix:
```
Automation sees: status='won', is_hit=None
Logic: status != 'pending' → Skip ✅
BUT ALSO: is_hit == None → Update! ❌
Result: OVERWRITES status to 'pending' or recalculates
```

### After Fix:
```
Automation sees: status='won', is_hit=True
Logic: status != 'pending' AND is_hit != None → Skip ✅
Result: PROTECTED - status remains 'won'
```

---

## Files Modified
1. `app.py` - `save_bet_to_db()` - Set `is_hit` when creating legs
2. `app.py` - `save_final_results_to_db()` - Set `is_hit` when manually saving results
3. `app.py` - `update_bet_from_espn()` - Set `is_hit` and add `is_hit is None` check
4. `app.py` - `update_bet_results_from_espn()` - Changed `OR` to `AND` in condition

---

## Migration Plan (if needed)

If existing legs have `status='won'/'lost'` but `is_hit=None`, run this SQL:

```sql
-- Set is_hit=True for all won legs
UPDATE bet_legs 
SET is_hit = TRUE 
WHERE status = 'won' AND is_hit IS NULL;

-- Set is_hit=False for all lost legs
UPDATE bet_legs 
SET is_hit = FALSE 
WHERE status = 'lost' AND is_hit IS NULL;

-- Verify
SELECT status, is_hit, COUNT(*) 
FROM bet_legs 
GROUP BY status, is_hit 
ORDER BY status, is_hit;
```

---

## Key Takeaway

**The `is_hit` column is the source of truth for whether a leg result has been determined.**

- `is_hit=None` → "I don't know yet, automation can calculate"
- `is_hit=True/False` → "I know the result, automation hands off"

All automation functions now respect this contract.
