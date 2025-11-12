# Manual Entry Form Update Summary

## Changes Made

### 1. File Picker Default (Instead of Camera)
**File:** `index.html` line 1582

**Change:** Removed `capture="environment"` attribute from file input
```html
<!-- Before -->
<input type="file" id="betslip-file-input" accept="image/*" capture="environment" style="display: none;">

<!-- After -->
<input type="file" id="betslip-file-input" accept="image/*" style="display: none;">
```

**Effect:** Mobile devices now open file gallery instead of camera when uploading bet slips.

---

### 2. "Add Bet" Dropdown Menu
**File:** `index.html` lines 1576-1594

**Change:** Replaced single "Upload Bet Slip" button with dropdown menu containing two options
```html
<button id="add-bet-button">➕ Add Bet ▼</button>
<div class="add-bet-dropdown" id="add-bet-dropdown" style="display: none;">
  <div class="dropdown-option" id="upload-betslip-option">📷 Upload Bet Slip</div>
  <div class="dropdown-option" id="manual-entry-option">✍️ Manual Entry</div>
</div>
```

**JavaScript:** Lines 4245-4289
- Dropdown toggles on button click
- "Upload Bet Slip" option opens file picker
- "Manual Entry" option redirects to `/add-bet.html`
- Clicking outside closes dropdown

---

### 3. Manual Entry Form Updates
**File:** `add-bet.html`

#### Added Fields (Lines 375-398)
1. **Bet Date** - Date picker for when bet was placed
   ```html
   <input type="date" id="bet-date" required>
   ```

2. **Potential Payout** - Auto-calculated readonly field
   ```html
   <input type="number" id="potential-payout" step="0.01" readonly>
   ```

3. **Secondary Bettors** - Search and select co-bettors
   ```html
   <input type="text" id="bettor-search-manual" placeholder="Type username or email...">
   <div id="bettor-suggestions-manual"></div>
   <div id="selected-bettors-manual"></div>
   ```

#### Auto-Calculation (Lines 495-565)
- Calculates payout from wager + odds
- Calculates odds from wager + payout
- Updates in real-time as user types
- Same logic as OCR modal

#### Secondary Bettors Autocomplete (Lines 567-665)
- `fetchAllUsers()` - Loads all users from `/api/users`
- Real-time search filtering by username or email
- Visual chips for selected bettors
- Remove button on each chip
- Same functionality as OCR modal

#### Updated Submit Function (Lines 667-900)
**New Data Structure:**
```javascript
const betData = {
  bet_id: document.getElementById('bet-id').value || `manual_${Date.now()}`,
  name: document.getElementById('bet-name').value,
  type: document.getElementById('bet-type').value,  // Maps to bet_type column
  betting_site: document.getElementById('betting-site').value,
  wager: parseFloat(document.getElementById('wager').value),  // Maps to wager column
  final_odds: oddsInput.value,  // Maps to final_odds column
  potential_winnings: parseFloat(payoutInput.value),  // Maps to potential_winnings column
  bet_date: document.getElementById('bet-date').value,
  secondary_bettor_ids: selectedSecondaryBettors.map(u => u.id),
  legs: [
    {
      game_date: '...',
      away_team: '...',
      home_team: '...',
      team: '...',
      player: '...',
      stat: '...',
      bet_type: '...',
      bet_line_type: 'over|under',
      line: 123.5,
      sport: '...',
      game_info: 'Away @ Home',
      odds: '-110',
      status: 'pending',
      leg_order: 0
    }
  ]
};
```

**Database Column Mapping:**
| Form Field | Database Column | Notes |
|------------|----------------|-------|
| `bet-id` | `bet_id` | Generated as `manual_${timestamp}` if empty |
| `bet-name` | `name` | User-provided name |
| `bet-type` | `bet_type` | Single, Parlay, etc. |
| `betting-site` | `betting_site` | DraftKings, FanDuel, etc. |
| `wager` | `wager` | Amount wagered |
| `odds` | `final_odds` | American odds format |
| `potential-payout` | `potential_winnings` | Auto-calculated |
| `bet-date` | `bet_date` | Date of bet placement |
| Secondary bettors | `bet_secondaries` table | Many-to-many relationship |

---

## Testing Checklist

### Manual Entry Path
- [ ] Navigate to homepage
- [ ] Click "➕ Add Bet" button
- [ ] Verify dropdown opens with two options
- [ ] Click "✍️ Manual Entry"
- [ ] Verify redirect to `/add-bet.html`
- [ ] Fill in all fields:
  - [ ] Bet ID (optional - auto-generates if empty)
  - [ ] Bet Name
  - [ ] Bet Type
  - [ ] Betting Site
  - [ ] Bet Date (date picker)
  - [ ] Wager amount
  - [ ] Odds (try entering)
  - [ ] Verify potential payout auto-calculates
  - [ ] OR enter payout and wager, verify odds calculate
- [ ] Search for secondary bettors:
  - [ ] Type username/email
  - [ ] Verify autocomplete suggestions appear
  - [ ] Click suggestion to add
  - [ ] Verify chip appears with remove button
  - [ ] Click X to remove bettor
- [ ] Add at least one leg:
  - [ ] Game date
  - [ ] Away team
  - [ ] Home team
  - [ ] Player name (if player prop)
  - [ ] Stat type
  - [ ] Over/Under
  - [ ] Target line
  - [ ] Sport
- [ ] Submit form
- [ ] Verify success notification
- [ ] Verify redirect to homepage
- [ ] Check that bet appears in "Live Bets"
- [ ] Click on bet to view details
- [ ] Verify all fields saved correctly
- [ ] Verify secondary bettors listed

### OCR Upload Path
- [ ] Navigate to homepage
- [ ] Click "➕ Add Bet" button
- [ ] Verify dropdown opens
- [ ] Click "📷 Upload Bet Slip"
- [ ] Verify file picker opens (NOT camera on mobile)
- [ ] Select image file
- [ ] Verify OCR modal opens with loading indicator
- [ ] Verify bet details populate from image
- [ ] Edit any field if needed
- [ ] Verify auto-calculation works
- [ ] Add secondary bettors
- [ ] Save bet
- [ ] Verify appears in "Live Bets"

---

## Known Issues / Notes

1. **No Python environment detected** - Need to install dependencies or use existing running server for testing
2. **Both paths use same endpoint** - `POST /api/bets` - ensures consistent database saving
3. **Leg structure updated** - Manual entry legs now include all fields that OCR legs have:
   - `away_team`, `home_team` (renamed from `away`, `home`)
   - `bet_type`, `bet_line_type` (stat type classification)
   - `line` (renamed from `target`)
   - `game_info`, `odds`, `status`, `leg_order`

---

## Next Steps

1. **Test in browser** - Start Flask server and test both pathways completely
2. **Mobile testing** - Verify file picker behavior on iOS/Android
3. **Database validation** - Check that manual entry bets have identical structure to OCR bets in database
4. **UI polish** - Ensure responsive design works on mobile for new fields
5. **Documentation** - Update user guide if needed
6. **Commit changes** - Push to GitHub after testing

---

## Files Modified

1. `index.html`
   - Line 1582: Removed `capture="environment"`
   - Lines 1576-1594: Added dropdown menu structure and CSS
   - Lines 4245-4289: Added dropdown JavaScript handlers

2. `add-bet.html`
   - Lines 375-398: Added bet-date, potential-payout, secondary-bettors fields
   - Lines 495-565: Added auto-calculation functions and listeners
   - Lines 567-665: Added secondary bettors autocomplete functionality
   - Lines 667-900: Updated submitBet() function with correct database mappings
