# How to Add bet_date for New Bets

## Quick Reference

When creating new bets manually or programmatically, always include the `bet_date` field.

---

## Format

```json
{
  "bet_id": "...",
  "betting_site": "...",
  "bet_date": "YYYY-MM-DD",
  "name": "...",
  "odds": "...",
  "wager": 0.0,
  "type": "...",
  "legs": [...]
}
```

**Key Points:**
- Format: `YYYY-MM-DD` (e.g., "2025-10-25")
- Place near top of bet object
- Represents when YOU placed the bet, not when games are played
- Typically 1-2 days before earliest game_date

---

## Examples

### Manual Entry Example
```json
{
  "bet_id": "DK123456789",
  "betting_site": "DraftKings",
  "bet_date": "2025-11-01",
  "name": "Week 9 Parlay",
  "odds": "+300",
  "wager": 10.0,
  "type": "Parlay",
  "legs": [
    {
      "game_date": "2025-11-03",
      "away": "Team A",
      "home": "Team B",
      "stat": "moneyline",
      "target": 1
    }
  ]
}
```

### Python Code Example
```python
from datetime import datetime, timedelta

# When creating a new bet
new_bet = {
    "bet_id": generate_bet_id(),
    "betting_site": "FanDuel",
    "bet_date": datetime.now().strftime('%Y-%m-%d'),  # Today's date
    "name": "My New Parlay",
    "odds": "+250",
    "wager": 20.0,
    "type": "Parlay",
    "legs": [...] 
}
```

---

## Deriving bet_date from game_date

If you don't know the exact bet placement date, use the earliest game date:

```python
def derive_bet_date_from_games(legs):
    """Derive bet_date from earliest game_date"""
    game_dates = [leg['game_date'] for leg in legs if 'game_date' in leg]
    
    if game_dates:
        earliest = min(game_dates)
        # Parse and subtract 1 day
        earliest_dt = datetime.strptime(earliest, '%Y-%m-%d')
        bet_date_dt = earliest_dt - timedelta(days=1)
        return bet_date_dt.strftime('%Y-%m-%d')
    
    # Fallback to current date
    return datetime.now().strftime('%Y-%m-%d')
```

---

## Common Scenarios

### 1. Adding Historical Bet (You know the date)
```json
"bet_date": "2025-09-15"  // The actual date you placed it
```

### 2. Adding Historical Bet (You don't know the date)
```json
"bet_date": "2025-09-22"  // Game was 9/23, so bet ~9/22
```

### 3. Adding New Bet Today
```json
"bet_date": "2025-11-01"  // Use today's date
```

### 4. Syncing from Render
Render should include bet_date in its response. If missing, the app will:
1. Try to extract from the bet_date field (not present)
2. Fall back to earliest game_date (from legs)
3. Parse from bet name if it has a date
4. Default to "2025-01-01"

---

## Validation Checklist

Before adding a bet, verify:
- ✅ bet_date is present
- ✅ Format is YYYY-MM-DD
- ✅ bet_date is before or equal to earliest game_date
- ✅ bet_date is not in the future (unless it's a future bet)

---

## Testing

After adding new bets, run:
```bash
python3 test_bet_date.py
```

This will verify:
- All bets have bet_date field
- Format is correct (YYYY-MM-DD)
- Field is at top level
- Operations preserve the field

---

## Troubleshooting

### Problem: Bet doesn't have bet_date after sync
**Solution:** Ensure Render includes bet_date in JSON. If not, update Render code to include it.

### Problem: bet_date format error
**Solution:** Ensure format is exactly `YYYY-MM-DD` (e.g., "2025-10-25", not "10/25/25")

### Problem: bet_date gets lost during operations
**Solution:** Run `test_bet_date.py` to identify which operation strips it. All current operations are verified to preserve it.

---

## Reference

See `BET_DATE_IMPLEMENTATION.md` for full technical details.
