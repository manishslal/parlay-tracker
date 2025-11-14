# Required Fields Audit for Bet Addition

## Overview

This document lists ALL fields that should be populated when adding new bets to ensure proper functionality of live data fetching, team name normalization, and frontend display.

---

## 🏆 Bets Table Required Fields

When inserting into the `bets` table:

### Core Fields
| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `user_id` | Integer | ✅ Yes | - | FK to users table |
| `bet_id` | String | ✅ Yes | - | Unique bet identifier from betting site |
| `bet_type` | String | ✅ Yes | `'parlay'` | `'parlay'`, `'sgp'`, `'single'` |
| `betting_site` | String | ✅ Yes | - | `'FanDuel'`, `'DraftKings'`, `'Bet365'`, `'Dabble'` |
| `bet_date` | String | ✅ Yes | - | Format: `YYYY-MM-DD` |
| `wager` | Numeric | ✅ Yes | - | Amount wagered |
| `odds` | Integer | ✅ Yes | - | American odds (e.g., `+442`) |
| `potential_payout` | Numeric | ✅ Yes | - | Wager + returns |
| `returns` | Numeric | ✅ Yes | - | Expected profit (payout - wager) |

### Status Fields
| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `status` | String | ⚠️ Auto | `'pending'` | Auto-calculated from legs |
| `is_active` | Boolean | ⚠️ Auto | `True` | `False` for historical bets |
| `is_archived` | Boolean | ⚠️ Auto | `False` | User-controlled archive status |
| `api_fetched` | String | ⚠️ Auto | `'No'` | `'Yes'` when completed |

### Leg Count Fields (Auto-calculated)
| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `total_legs` | Integer | ⚠️ Auto | `0` | Total number of legs |
| `legs_won` | Integer | ⚠️ Auto | `0` | Count of won legs |
| `legs_lost` | Integer | ⚠️ Auto | `0` | Count of lost legs |
| `legs_pending` | Integer | ⚠️ Auto | `0` | Count of pending legs |
| `legs_live` | Integer | ⚠️ Auto | `0` | Count of live legs |

### Sharing Fields (Bet Sharing V2)
| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `secondary_bettors` | Array | 🔷 Optional | `[]` | User IDs of secondary bettors |
| `watchers` | Array | 🔷 Optional | `[]` | User IDs of watchers (view-only) |

---

## 📊 Bet_Legs Table Required Fields

When inserting into the `bet_legs` table (one row per leg):

### Player/Team Info
| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `bet_id` | Integer | ✅ Yes | - | FK to bets table |
| `player_name` | String | ✅ Yes | - | Player name or team name |
| `player_team` | String | ⚠️ Normalized | - | **Abbreviation** (e.g., `'DET'`, `'OKC'`) - normalized on startup |
| `player_position` | String | 🔷 Optional | - | Position abbreviation (e.g., `'WR'`, `'QB'`) |
| `player_id` | Integer | 🔷 Optional | - | FK to players table (if exists) |

### Game Info
| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `home_team` | String | ✅ Yes | - | **Nickname** (e.g., `'Lions'`, `'Thunder'`) - normalized on startup |
| `away_team` | String | ✅ Yes | - | **Nickname** (e.g., `'Bills'`, `'Lakers'`) - normalized on startup |
| `game_date` | Date | ✅ Yes | - | Date of the game |
| `game_time` | Time | 🔷 Optional | - | Game start time |
| `game_id` | String | 🔷 Optional | - | ESPN game ID |
| `game_status` | String | ⚠️ Auto | - | `'STATUS_SCHEDULED'`, `'STATUS_IN_PROGRESS'`, `'STATUS_FINAL'` |
| `sport` | String | **✅ REQUIRED** | `'NFL'` | **CRITICAL**: `'NFL'`, `'NBA'`, `'MLB'`, `'NHL'`, etc. |

### Bet Details
| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `bet_type` | String | ✅ Yes | - | Stat type (e.g., `'spread'`, `'moneyline'`, `'receiving_yards'`) |
| `bet_line_type` | String | 🔷 Optional | - | `'over'`, `'under'` (for props) |
| `target_value` | Numeric | ✅ Yes | - | Target number to beat |
| `achieved_value` | Numeric | ⚠️ Auto | - | Final stat value (populated on game completion) |
| `leg_order` | Integer | ✅ Yes | - | Order of leg in parlay (1, 2, 3...) |

### Status Fields
| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `status` | String | ⚠️ Auto | `'pending'` | `'pending'`, `'won'`, `'lost'` - updated on completion |
| `is_hit` | Boolean | ⚠️ Auto | `None` | `True` (won) or `False` (lost) - updated on completion |

### Odds Fields
| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `original_leg_odds` | Integer | 🔷 Optional | - | Original leg odds |
| `boosted_leg_odds` | Integer | 🔷 Optional | - | Boosted odds (if applicable) |
| `final_leg_odds` | Integer | 🔷 Optional | - | Final odds used |

### Live Game Data (Auto-populated)
| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `home_score` | Integer | ⚠️ Auto | - | Home team score (updated live) |
| `away_score` | Integer | ⚠️ Auto | - | Away team score (updated live) |
| `current_quarter` | String | ⚠️ Auto | - | Current period/quarter |
| `time_remaining` | String | ⚠️ Auto | - | Time left in period |

---

## 🎯 Field Categories Explained

### ✅ **Required** - MUST populate when creating bet
- Missing these will cause errors or broken functionality
- Examples: `player_name`, `home_team`, `away_team`, `game_date`, `bet_type`, `target_value`, `sport`

### ⚠️ **Auto** - Automatically calculated/populated by system
- Don't manually set these - let the system handle them
- Examples: `status`, `is_hit`, `achieved_value`, `game_status`, `legs_won`, `legs_lost`

### 🔷 **Optional** - Nice to have but not required
- Enhances display or provides extra context
- Examples: `player_position`, `player_id`, `odds` fields

### ⚠️ **Normalized** - Will be normalized on startup
- Initial value can be abbreviation, full name, or nickname
- Startup automation will standardize these
- Examples: `home_team` → nickname, `away_team` → nickname, `player_team` → abbreviation

---

## 🚨 CRITICAL: The `sport` Field

### Why `sport` is Now REQUIRED

**Problem**: Without `sport`, the team name normalization runs blind:
- NFL bet with missing `sport` → defaults to `'NFL'` ✅ (correct)
- NBA bet with missing `sport` → defaults to `'NFL'` ❌ (WRONG!)
- Result: NBA bets get NFL team names, breaking everything

**Solution**: **ALWAYS populate `sport` for every leg**

### Sport-Aware Normalization (Added Nov 2025)

The startup automation now:
1. Reads the `sport` field from each bet_leg
2. Uses sport-specific team lookups
3. Normalizes to the correct sport's teams

**Example**:
```python
# NFL leg - sport='NFL'
{
    "home_team": "DET",          # ← Will normalize to "Lions" (NFL)
    "away_team": "Buffalo Bills", # ← Will normalize to "Bills" (NFL)
    "player_team": "Detroit Lions", # ← Will normalize to "DET" (NFL abbreviation)
    "sport": "NFL"  # ← REQUIRED for correct normalization
}

# NBA leg - sport='NBA'
{
    "home_team": "DET",             # ← Will normalize to "Pistons" (NBA)
    "away_team": "Oklahoma City Thunder", # ← Will normalize to "Thunder" (NBA)
    "player_team": "Detroit Pistons", # ← Will normalize to "DET" (NBA abbreviation)
    "sport": "NBA"  # ← REQUIRED for correct normalization
}
```

### What Happens Without `sport`?

If you add a bet without the `sport` field:

**Old Behavior (Before Nov 2025)**:
- Defaults to NFL API
- NBA games show 0-0 scores
- No live data updates

**New Behavior (After Nov 2025)**:
- Defaults to NFL normalization
- NBA bet gets NFL team names
- Example: Detroit Pistons game → normalized to "Lions" (NFL) instead of "Pistons" (NBA)
- **Data corruption!**

---

## 📋 Insertion Checklist

Before running a bet insertion script, verify:

### Bets Table
- [ ] `user_id` is valid
- [ ] `bet_id` is unique and matches betting site format
- [ ] `bet_type` is `'parlay'`, `'sgp'`, or `'single'`
- [ ] `betting_site` is `'FanDuel'`, `'DraftKings'`, `'Bet365'`, or `'Dabble'`
- [ ] `bet_date` is in `YYYY-MM-DD` format
- [ ] `wager`, `odds`, `potential_payout`, `returns` are correct numbers

### Bet_Legs Table (for EACH leg)
- [ ] `bet_id` matches parent bet
- [ ] `player_name` is populated (player or team name)
- [ ] `home_team` is full team name or nickname
- [ ] `away_team` is full team name or nickname
- [ ] `game_date` is in `YYYY-MM-DD` format
- [ ] `bet_type` is lowercase (e.g., `'spread'`, not `'SPREAD'`)
- [ ] `target_value` is a number
- [ ] `leg_order` is sequential (1, 2, 3...)
- [ ] **`sport` is populated with correct sport code** ⚠️ **CRITICAL**

### Sport-Specific Verification
- [ ] NFL bets: `sport='NFL'`
- [ ] NBA bets: `sport='NBA'`
- [ ] MLB bets: `sport='MLB'`
- [ ] NHL bets: `sport='NHL'`
- [ ] College Football: `sport='NCAAF'`
- [ ] College Basketball: `sport='NCAAB'`

---

## 🔧 Automation Impact

These automations rely on properly populated fields:

### 1. Team Name Normalization (Startup)
**Requires**: `sport`, `home_team`, `away_team`, `player_team`
- Normalizes team names to nicknames and abbreviations
- Uses `sport` to select correct league's teams
- Runs on every app startup

### 2. Bet Leg Auto-Updates (Every 5 Minutes)
**Requires**: `status='completed'`, `game_status='STATUS_FINAL'`, `sport`, `game_date`
- Updates `achieved_value` from ESPN API
- Calculates `status` (won/lost) and `is_hit` (True/False)
- Uses `sport` to call correct ESPN API

### 3. Auto-Move to Historical (On Page Load)
**Requires**: `status`, `is_active`, all leg statuses
- Moves completed bets to historical view
- Updates final game results

### 4. Daily Team Data Update (2 AM)
**Requires**: Teams table properly populated
- Updates team standings, records, playoff seeds
- Used by team name normalization

---

## 📝 Summary

**Minimum Required Fields for New Bet**:

**Bets Table**:
- `user_id`, `bet_id`, `bet_type`, `betting_site`, `bet_date`
- `wager`, `odds`, `potential_payout`, `returns`

**Bet_Legs Table** (per leg):
- `bet_id`, `player_name`, `home_team`, `away_team`
- `game_date`, `bet_type`, `target_value`, `leg_order`
- **`sport`** ← **CRITICAL! Must always be populated!**

**New as of Nov 2025**:
- `sport` field is now **MANDATORY** for all new bets
- Startup automation uses `sport` for team name normalization
- Without `sport`, wrong sport's teams will be used
- This prevents NBA teams from overwriting NFL teams and vice versa
