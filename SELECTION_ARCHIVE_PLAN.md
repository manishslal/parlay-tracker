# Selection-Based Archive System Implementation Plan

## Database Schema Changes ✅ COMPLETED

### New Columns Added:
- `is_active` (Boolean, default=True): 1=Live Bets, 0=Historical/Archived
- `is_archived` (Boolean, default=False): 1=Archived, 0=Not Archived

### Bet Distribution Logic:
| is_active | is_archived | Tab |
|-----------|-------------|-----|
| 1 | 0 | **Live Bets** |
| 0 | 0 | **Historical Bets** |
| * | 1 | **Archived Bets** |

## Backend API Changes Needed

### 1. Update Existing Endpoints
- `/todays` - Filter by `is_active=1, is_archived=0`
- `/live` - Filter by `is_active=1, is_archived=0` 
- `/historical` - Filter by `is_active=0, is_archived=0`
- `/api/archived` - Filter by `is_archived=1` (regardless of is_active)

### 2. New Bulk Action Endpoints

**POST `/api/bets/bulk-archive`**
```json
Request: { "bet_ids": [1, 2, 3] }
Response: { "success": true, "archived_count": 3 }
```
- Sets `is_archived=1` for all specified bet IDs
- Updates `updated_at` timestamp

**POST `/api/bets/bulk-unarchive`**
```json
Request: { "bet_ids": [1, 2, 3] }
Response: { "success": true, "unarchived_count": 3 }
```
- Sets `is_archived=0` for all specified bet IDs
- Returns bets to Historical tab (is_active=0, is_archived=0)

## Frontend UI Changes

### 1. Remove Individual Archive Buttons ✅
- Delete the 📦 button code from render function
- Remove archive button styling and event handlers

### 2. Add Select/Selected Button with Dropdown

**Location**: Next to "Collapse All" button in toolbar

**Button States**:
- "Select" - Default state when no bets selected
- "Selected (X)" - Shows count when bets are selected

**Dropdown Menu Items**:
- For Live/Historical tabs: "Archive Selected", "Unselect All"
- For Archived tab: "Unarchive Selected", "Unselect All"

**HTML Structure**:
```html
<div class="selection-controls">
  <button id="select-btn" class="select-button">
    Select
    <span class="dropdown-icon">▼</span>
  </button>
  <div id="select-dropdown" class="select-dropdown">
    <button class="dropdown-item" data-action="archive">Archive Selected</button>
    <button class="dropdown-item" data-action="unselect">Unselect All</button>
  </div>
</div>
```

### 3. Press-and-Hold Selection

**Interaction Pattern**:
- **Press and hold** bet header for ~500ms → Select bet
- **Tap selected bet** header → Deselect bet
- **Tap unselected bet** header (when nothing selected) → Expand/collapse (normal behavior)
- **Tap unselected bet** header (when others selected) → Select bet (no expand/collapse)

**Implementation**:
```javascript
let pressTimer = null;
let selectionMode = false; // True when any bet is selected

header.addEventListener('touchstart', (e) => {
  if (!selectionMode) {
    // Start press-and-hold timer
    pressTimer = setTimeout(() => {
      selectBet(betId);
      selectionMode = true;
    }, 500);
  }
});

header.addEventListener('touchend', (e) => {
  clearTimeout(pressTimer);
  
  if (selectionMode) {
    // In selection mode: toggle selection
    toggleBetSelection(betId);
  } else {
    // Normal mode: expand/collapse
    toggleBetExpansion(section);
  }
});
```

### 4. Selection Visual Styling

**Selected Bet Appearance**:
```css
.parlay-section.selected {
  transform: scale(0.95);
  border: 3px solid #fff;
  box-shadow: 0 0 15px rgba(255, 255, 255, 0.5);
  transition: transform 0.2s ease, border 0.2s ease;
}
```

**Animation**:
- Smooth scale-down to 95%
- Thick white border appears
- Glow effect for visibility

### 5. Selection State Management

**Global State**:
```javascript
const selectedBets = new Set(); // Stores selected bet IDs

function updateSelectButton() {
  const btn = document.getElementById('select-btn');
  const count = selectedBets.size;
  
  if (count === 0) {
    btn.textContent = 'Select ▼';
    btn.classList.remove('has-selection');
  } else {
    btn.textContent = `Selected (${count}) ▼`;
    btn.classList.add('has-selection');
  }
}

function selectBet(betId) {
  selectedBets.add(betId);
  document.querySelector(`[data-bet-id="${betId}"]`).classList.add('selected');
  updateSelectButton();
}

function deselectBet(betId) {
  selectedBets.delete(betId);
  document.querySelector(`[data-bet-id="${betId}"]`).classList.remove('selected');
  updateSelectButton();
}

function clearAllSelections() {
  document.querySelectorAll('.parlay-section.selected').forEach(section => {
    section.classList.remove('selected');
  });
  selectedBets.clear();
  updateSelectButton();
}
```

### 6. Archive/Unarchive Actions

```javascript
async function archiveSelectedBets() {
  if (selectedBets.size === 0) {
    alert('No bets selected');
    return;
  }
  
  const betIds = Array.from(selectedBets);
  
  try {
    const response = await fetchWithAdminToken(`${API_BASE}/api/bets/bulk-archive`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ bet_ids: betIds })
    });
    
    if (!response.ok) throw new Error('Failed to archive bets');
    
    const result = await response.json();
    msg.textContent = `✅ Archived ${result.archived_count} bet(s)`;
    
    clearAllSelections();
    await update(); // Refresh display
  } catch (err) {
    console.error('Error archiving bets:', err);
    alert('Failed to archive bets: ' + err.message);
  }
}

async function unarchiveSelectedBets() {
  // Similar to archiveSelectedBets but calls /api/bets/bulk-unarchive
}
```

## User Flow Examples

### Scenario 1: Archive from Historical
1. User goes to "Historical Bets" tab
2. Press and hold on a bet header for 500ms
3. Bet scales down to 95%, gets white border
4. "Select" button changes to "Selected (1)"
5. User taps other bets to select more
6. User clicks "Selected (3)" → dropdown appears
7. User clicks "Archive Selected"
8. Confirmation: "Archive 3 bets?"
9. Bets move to "Archived Bets" tab
10. Historical tab refreshes, selected bets gone

### Scenario 2: Unarchive from Archived
1. User goes to "Archived Bets" tab
2. Press and hold to select archived bets
3. Click "Selected (5)" → "Unarchive Selected"
4. Bets return to "Historical Bets" tab
5. Archived tab refreshes

### Scenario 3: Cancel Selection
1. User selects multiple bets
2. Changes mind
3. Clicks "Selected (X)" → "Unselect All"
4. All selections cleared
5. Button returns to "Select"

## Implementation Order

1. ✅ Update models.py with new columns
2. ✅ Run migration to add columns
3. ⏳ Update API endpoints filtering logic
4. ⏳ Add bulk archive/unarchive endpoints
5. ⏳ Remove individual archive buttons from frontend
6. ⏳ Add Select/Selected button with dropdown
7. ⏳ Implement press-and-hold selection
8. ⏳ Add selection visual styling (CSS)
9. ⏳ Wire up dropdown actions
10. ⏳ Test complete flow

## CSS Additions Needed

```css
/* Select button */
.select-button {
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
}

.select-button.has-selection {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

/* Dropdown */
.select-dropdown {
  display: none;
  position: absolute;
  top: 100%;
  left: 0;
  background: #1a1a2e;
  border: 1px solid #333;
  border-radius: 6px;
  min-width: 200px;
  z-index: 1000;
  margin-top: 0.5rem;
}

.select-dropdown.active {
  display: block;
}

.dropdown-item {
  width: 100%;
  padding: 0.75rem 1rem;
  background: none;
  border: none;
  color: #fff;
  text-align: left;
  cursor: pointer;
}

.dropdown-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

/* Selected bet styling */
.parlay-section.selected {
  transform: scale(0.95);
  border: 3px solid #fff !important;
  box-shadow: 0 0 15px rgba(255, 255, 255, 0.5);
  transition: all 0.2s ease;
}

/* Prevent text selection during press-and-hold */
.parlay-header {
  -webkit-user-select: none;
  user-select: none;
  -webkit-touch-callout: none;
}
```

## Notes

- Press-and-hold time: 500ms (standard for mobile apps)
- Selection persists when switching between tabs (optional)
- Max selections: No limit
- Bulk archive is much faster than individual archives
- White border chosen for high contrast in both light/dark modes
