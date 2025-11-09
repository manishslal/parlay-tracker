# API Endpoint Update Guide

## Quick Reference: Switching to Structured Database

This guide shows exactly how to update each API endpoint to use the new `to_dict_structured()` method.

---

## 1. `/todays` Endpoint

**Location:** `app.py` line ~1303-1318

**Current Code:**
```python
@app.route('/todays')
@login_required
def todays():
    """Get today's parlays"""
    try:
        # Get user's today's bets
        bets = get_user_bets_query(current_user, is_active=True, status='pending').all()
        
        # Convert to dict format
        todays_parlays = [bet.to_dict() for bet in bets]
        
        return jsonify(todays_parlays), 200
    except Exception as e:
        app.logger.error(f"Error getting today's parlays: {str(e)}")
        return jsonify({'error': 'Failed to load todays parlays'}), 500
```

**Updated Code:**
```python
@app.route('/todays')
@login_required
def todays():
    """Get today's parlays"""
    try:
        # Get user's today's bets
        bets = get_user_bets_query(current_user, is_active=True, status='pending').all()
        
        # Convert to dict format using structured database
        todays_parlays = [bet.to_dict_structured() for bet in bets]
        
        return jsonify(todays_parlays), 200
    except Exception as e:
        app.logger.error(f"Error getting today's parlays: {str(e)}")
        return jsonify({'error': 'Failed to load todays parlays'}), 500
```

**Change:** Line 9 - `bet.to_dict()` → `bet.to_dict_structured()`

---

## 2. `/live` Endpoint

**Location:** `app.py` line ~1286-1295

**Current Code:**
```python
@app.route('/live')
@login_required
def live():
    """Get live parlays"""
    bets = get_user_bets_query(current_user, is_active=True, status='live').all()
    live_parlays = [bet.to_dict() for bet in bets]
    return jsonify(live_parlays), 200
```

**Updated Code:**
```python
@app.route('/live')
@login_required
def live():
    """Get live parlays"""
    bets = get_user_bets_query(current_user, is_active=True, status='live').all()
    live_parlays = [bet.to_dict_structured() for bet in bets]
    return jsonify(live_parlays), 200
```

**Change:** Line 6 - `bet.to_dict()` → `bet.to_dict_structured()`

---

## 3. `/historical` Endpoint

**Location:** `app.py` line ~1321-1340

**Current Code:**
```python
@app.route('/historical')
@login_required
def historical():
    """Get historical (completed) parlays"""
    try:
        # Get completed bets (not active, not archived)
        bets = get_user_bets_query(
            current_user, 
            is_active=False
        ).filter(
            Bet.is_archived == False
        ).all()
        
        historical_parlays = [bet.to_dict() for bet in bets]
        
        return jsonify(historical_parlays), 200
    except Exception as e:
        app.logger.error(f"Error getting historical parlays: {str(e)}")
        return jsonify({'error': 'Failed to load historical parlays'}), 500
```

**Updated Code:**
```python
@app.route('/historical')
@login_required
def historical():
    """Get historical (completed) parlays"""
    try:
        # Get completed bets (not active, not archived)
        bets = get_user_bets_query(
            current_user, 
            is_active=False
        ).filter(
            Bet.is_archived == False
        ).all()
        
        historical_parlays = [bet.to_dict_structured() for bet in bets]
        
        return jsonify(historical_parlays), 200
    except Exception as e:
        app.logger.error(f"Error getting historical parlays: {str(e)}")
        return jsonify({'error': 'Failed to load historical parlays'}), 500
```

**Change:** Line 14 - `bet.to_dict()` → `bet.to_dict_structured()`

---

## 4. `/api/archived` Endpoint

**Location:** `app.py` (search for "archived" route)

**Current Code:**
```python
@app.route('/api/archived')
@login_required
def get_archived():
    """Get archived bets"""
    try:
        bets = get_user_bets_query(current_user).filter(
            Bet.is_archived == True
        ).all()
        
        archived_bets = [bet.to_dict() for bet in bets]
        
        return jsonify(archived_bets), 200
    except Exception as e:
        app.logger.error(f"Error getting archived bets: {str(e)}")
        return jsonify({'error': 'Failed to load archived bets'}), 500
```

**Updated Code:**
```python
@app.route('/api/archived')
@login_required
def get_archived():
    """Get archived bets"""
    try:
        bets = get_user_bets_query(current_user).filter(
            Bet.is_archived == True
        ).all()
        
        archived_bets = [bet.to_dict_structured() for bet in bets]
        
        return jsonify(archived_bets), 200
    except Exception as e:
        app.logger.error(f"Error getting archived bets: {str(e)}")
        return jsonify({'error': 'Failed to load archived bets'}), 500
```

**Change:** Line 10 - `bet.to_dict()` → `bet.to_dict_structured()`

---

## Feature Flag Approach (Recommended)

For safer deployment, add a feature flag to toggle between methods:

```python
# At top of app.py
USE_STRUCTURED_DATA = os.environ.get('USE_STRUCTURED_DATA', 'false').lower() == 'true'

def get_bet_dict(bet):
    """Get bet dictionary using appropriate method"""
    if USE_STRUCTURED_DATA:
        return bet.to_dict_structured()
    else:
        return bet.to_dict()

# Then in endpoints:
@app.route('/todays')
@login_required
def todays():
    bets = get_user_bets_query(current_user, is_active=True, status='pending').all()
    todays_parlays = [get_bet_dict(bet) for bet in bets]
    return jsonify(todays_parlays), 200
```

**Enable structured data:**
```bash
# In Render environment variables
USE_STRUCTURED_DATA=true
```

---

## Testing Checklist

Before deploying each endpoint update:

### Backend Testing
- [ ] Query returns correct number of bets
- [ ] All legs present in response
- [ ] Jersey numbers appear in leg data
- [ ] Team abbreviations correct (BAL, KC, MIA, etc.)
- [ ] Financial data accurate (wager, odds, returns)
- [ ] Status fields correct (pending, live, won, lost)

### Frontend Testing
- [ ] Bets display correctly in UI
- [ ] Player names render properly
- [ ] Team names show correctly
- [ ] Leg stats display (target, current, status)
- [ ] Status colors work (pending/live/won/lost)
- [ ] No JavaScript console errors

### Data Validation
- [ ] Compare old vs new response for same bet
- [ ] Verify leg count matches
- [ ] Check all required fields present
- [ ] Validate JSON structure matches frontend expectations

---

## Rollout Plan

### Phase 1: Test on Development
1. Update `/todays` endpoint first
2. Test thoroughly with real data
3. Verify frontend compatibility
4. Check for any errors in logs

### Phase 2: Staged Rollout
1. Deploy `/todays` (most frequently used)
2. Monitor for 24 hours
3. Deploy `/live` 
4. Monitor for 24 hours
5. Deploy `/historical` and `/archived`

### Phase 3: Cleanup
1. Remove old `to_dict()` calls
2. Update documentation
3. Consider deprecating JSON blob (keep as backup)

---

## Rollback Plan

If issues arise, revert is simple:

```python
# Change back to:
todays_parlays = [bet.to_dict() for bet in bets]
```

Or with feature flag:
```bash
# In Render environment variables
USE_STRUCTURED_DATA=false
```

---

## Expected Benefits

After all endpoints updated:

✅ **Jersey numbers** visible in UI  
✅ **Current team data** from ESPN API  
✅ **Better performance** (indexed database queries)  
✅ **Data consistency** (no JSON parsing errors)  
✅ **Future-ready** for new features (player photos, team logos)

---

## Need Help?

Reference files:
- `DATABASE_INTEGRATION_COMPLETE.md` - Full implementation details
- `FRONTEND_DB_MAPPING.md` - Field mappings
- `models.py` - See `to_dict_structured()` implementation
- `test_structured_dict_production.py` - Test script example
