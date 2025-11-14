# Bet365 Logo Support Added ✅

**Date:** November 11, 2025

## Changes Made

### 1. Frontend Display (index.html)
- ✅ Added `'Bet365': 'bet365'` to `logoMap` (line ~3814)
- ✅ Added `--bet365: #ffcc00;` CSS variable for Bet365 brand color
- ✅ Logo automatically switches based on theme:
  - **Dark mode**: Uses `bet365-logo-1.svg` (white/light version)
  - **Light mode**: Uses `bet365-logo-2.svg` (colored version)

### 2. Add Bet Form (add-bet.html)
- ✅ Added `<option value="Bet365">Bet365</option>` to betting site dropdown
- ✅ Positioned after DraftKings, before BetMGM

### 3. Documentation (BET_ADDITION_CHECKLIST.md)
- ✅ Added Bet365 to valid betting_site values list
- ✅ Updated all references from "FanDuel/DraftKings/Dabble" to include Bet365
- ✅ Updated validation checklist
- ✅ Added note about logo changing based on dark/light mode

### 4. Logo Files (Already Present)
- ✅ `media/logos/bet365-logo-1.svg` (15KB) - White/light version for dark mode
- ✅ `media/logos/bet365-logo-2.svg` (24KB) - Colored version for light mode

## How It Works

### Logo Display Logic
```javascript
const isDarkMode = !document.body.classList.contains('light-mode');
const logoSuffix = isDarkMode ? '1' : '2'; // 1=white, 2=colored

const logoMap = {
  'DraftKings': 'draftkings',
  'FanDuel': 'fanduel',
  'Bet365': 'bet365',  // NEW
  'Dabble': 'dabble'
};

const logoKey = logoMap[siteText];
const logoHTML = `<img src="media/logos/${logoKey}-logo-${logoSuffix}.svg" ...>`;
```

### Theme-Based Logo Selection
- **Dark Mode**: 
  - Bet365 → `media/logos/bet365-logo-1.svg` (white)
  - FanDuel → `media/logos/fanduel-logo-1.svg` (white)
  - DraftKings → `media/logos/draftkings-logo-1.svg` (white)

- **Light Mode**:
  - Bet365 → `media/logos/bet365-logo-2.svg` (colored)
  - FanDuel → `media/logos/fanduel-logo-2.svg` (colored)
  - DraftKings → `media/logos/draftkings-logo-2.svg` (colored)

## Usage

### Adding a Bet365 Bet
```python
bet_data = {
    "bet_id": "BET365-12345",
    "name": "Sunday NFL Parlay",
    "type": "Parlay",
    "betting_site": "Bet365",  # Displays Bet365 logo
    "bet_date": "2025-11-11",
    "wager": 10,
    "odds": 450,
    "returns": 45,
    "legs": [...]
}
```

### Frontend Display
- **Footer**: Shows Bet365 logo (theme-appropriate)
- **Betting Site Filter**: Bet365 appears in filter dropdown (auto-generated)
- **Color**: Uses `--bet365` CSS variable (#ffcc00 - yellow)

## Filter Integration

The betting site filter is dynamically generated from all visible bets:
```javascript
const sites = new Set();
document.querySelectorAll('.parlay-section').forEach(section => {
  const site = section.dataset.site;
  if (site) sites.add(site);
});
```

Once a Bet365 bet is added, "Bet365" will automatically appear in the betting site filter menu.

## Testing Checklist

To verify Bet365 logo support:

- [ ] Add a test bet with `"betting_site": "Bet365"`
- [ ] Verify logo appears in footer in **dark mode** (white version)
- [ ] Toggle to **light mode**, verify logo changes to colored version
- [ ] Check that "Bet365" appears in betting site filter dropdown
- [ ] Verify filtering by "Bet365" shows only Bet365 bets
- [ ] Confirm logo doesn't break if bet_id format is different

## Supported Betting Sites

| Site | Logo File Prefix | Color Variable | Auto-Detect |
|------|-----------------|----------------|-------------|
| FanDuel | `fanduel-logo` | `--fanduel: #2196f3` | bet_id starts with `O/` |
| DraftKings | `draftkings-logo` | `--draftkings: #4caf50` | bet_id starts with `DK` |
| Bet365 | `bet365-logo` | `--bet365: #ffcc00` | No auto-detect |
| Dabble | `dabble-logo` | `--dabble: #ffc107` | No auto-detect |

## Notes

- Logo files must be SVG format with `-1.svg` (dark) and `-2.svg` (light) suffixes
- If logo file is missing, the `onerror` handler hides the broken image
- Betting site name still displays even if logo is missing
- Filter menu dynamically updates based on actual bets in the system
