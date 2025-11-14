# OCR to Database Field Mapping

## ✅ CORRECTED MAPPINGS

### Bet-Level Fields (OCR → `bets` table)

| OCR Field | bet_data Key | DB Column | Status | Notes |
|-----------|--------------|-----------|--------|-------|
| `bet_id` (from screenshot) | `bet_id` | `bets.bet_id` | ✅ **FIXED** | Now extracts from screenshot, falls back to `ocr_xxxxxxxx` |
| `bet_type` | `type` | `bets.bet_type` | ✅ **FIXED** | Correctly maps to `bet_type` column |
| `wager_amount` | `wager` | `bets.wager` | ✅ **FIXED** | Changed from `stake` to `wager` |
| `potential_payout` | `potential_winnings` | `bets.potential_winnings` | ✅ **FIXED** | Changed from `potential_return` to `potential_winnings` |
| `total_odds` | `final_odds` | `bets.final_odds` | ✅ **FIXED** | Changed from `american_odds` to `final_odds` (parsed as integer) |
| `bet_site` | `betting_site` | `bets.betting_site` | ✅ MAPPED | Already correct |
| `bet_date` | `bet_date` | `bets.bet_date` | ✅ MAPPED | Already correct |
| `bet_name` | `name` | `bet_data` JSON only | ⚠️ JSON-only | Not a direct DB column |
| Upload timestamp | `notes` | `bets.created_at` | ✅ **FIXED** | `created_at` is auto-populated by DB, notes stored in JSON |
| Current user | N/A | `bets.user_id` | ✅ MAPPED | Set via `save_bet_to_db(user_id)` |
| Secondary bettors | `secondary_bettor_ids` | `bets.secondary_bettors` | ✅ MAPPED | ARRAY of user IDs |

### Leg-Level Fields (OCR → `bet_legs` table)

| OCR Field | bet_data Key | DB Column | Status | Notes |
|-----------|--------------|-----------|--------|-------|
| `leg.bet_type` | `bet_type` | `bet_legs.bet_type` | ✅ **FIXED** | Changed from `type` to `bet_type` |
| `leg.bet_line_type` | `bet_line_type` | `bet_legs.bet_line_type` | ✅ **FIXED** | Changed from `over_under` to `bet_line_type` |
| `leg.player_name` | `player` | `bet_legs.player_name` | ✅ MAPPED | Already correct |
| `leg.team_name` | `team` | `bet_legs.player_team` | ✅ MAPPED | Maps to `player_team` column |
| `leg.home_team` | `home_team` | `bet_legs.home_team` | ✅ MAPPED | Already correct |
| `leg.away_team` | `away_team` | `bet_legs.away_team` | ✅ MAPPED | Already correct |
| `leg.sport` | `sport` | `bet_legs.sport` | ✅ MAPPED | Already correct |
| `leg.stat_type` | `stat` | `bet_legs.stat_type` | ✅ MAPPED | Already correct |
| `leg.target_value` | `line` | `bet_legs.target_value` | ✅ MAPPED | Already correct |
| `leg.odds` | `odds` | `bet_legs.final_leg_odds` | ✅ MAPPED | Parsed as integer |
| `leg.game_date` | `game_date` | `bet_legs.game_date` | ✅ MAPPED | Parsed to date type |
| `leg.game_date` | `game_date` | `bet_legs.game_time` | ✅ MAPPED | Time portion extracted |
| `leg.game_info` | `game_info` | `bet_data` JSON only | ⚠️ JSON-only | Not a direct DB column |
| Leg order | `leg_order` | `bet_legs.leg_order` | ✅ MAPPED | Auto-generated (0, 1, 2...) |
| Status | `status` | `bet_legs.status` | ✅ MAPPED | Defaults to 'pending' |

---

## ❌ FIELDS NOT SAVED TO DATABASE COLUMNS

These fields are stored in the `bet_data` JSON column but **NOT** in structured database columns:

### Bet-Level JSON-Only Fields
- ✅ `name` - Bet name is in JSON only (no direct column)
- ✅ `notes` - OCR upload timestamp is in JSON only
- ✅ `source` - "ocr" marker is in JSON only

### Leg-Level JSON-Only Fields
- ✅ `game_info` - "Away @ Home" string is in JSON only (home_team/away_team are stored separately)

---

## 📊 AVAILABLE BUT UNUSED DATABASE COLUMNS

These columns exist in the database but are **NOT** currently populated by OCR:

### `bets` Table - Unpopulated Columns
| Column | Type | Why Not Used |
|--------|------|--------------|
| `actual_winnings` | Numeric(10,2) | Only set after bet is resolved |
| `is_active` | Boolean | Managed by system (defaults to True) |
| `is_archived` | Boolean | User action, not from OCR |
| `api_fetched` | String | Set when ESPN API fetches stats |
| `legs_won`, `legs_lost`, `legs_pending`, `legs_live` | Integer | Calculated when games complete |
| `watchers` | ARRAY(Integer) | User-added, not from OCR |

### `bet_legs` Table - Unpopulated Columns
| Column | Type | Why Not Used |
|--------|------|--------------|
| `player_id` | Integer (FK) | Requires player lookup/matching |
| `player_position` | String | Not visible on bet slips |
| `game_id` | String | ESPN-specific, requires API |
| `game_status` | String | Real-time data from ESPN |
| `parlay_sport` | String | Legacy field |
| `is_home_game` | Boolean | Can be inferred but not critical |
| `achieved_value` | Numeric | Only known after game ends |
| `player_season_avg`, `player_last_5_avg`, `vs_opponent_avg` | Numeric | Requires stats lookup |
| `original_leg_odds`, `boosted_leg_odds` | Integer | OCR only sees final odds |
| `is_hit` | Boolean | Calculated when game ends |
| `void_reason` | String | Only set if leg voided |
| `current_quarter`, `time_remaining` | String | Live game data from ESPN |
| `home_score`, `away_score` | Integer | Live/final scores from ESPN |
| `weather_conditions` | String | Not on bet slips |
| `injury_during_game` | Boolean | Real-time data |
| `dnp_reason` | String | Only if player doesn't play |

---

## 🔄 DATA FLOW SUMMARY

### 1. **GPT-4 Vision Extraction**
```json
{
  "bet_id": "DK-12345678",
  "bet_site": "DraftKings",
  "bet_type": "parlay",
  "total_odds": "+450",
  "wager_amount": 20.00,
  "potential_payout": 110.00,
  "legs": [...]
}
```

### 2. **Frontend Editing** (User can modify)
- ✅ All fields editable in modal
- ✅ Auto-calculations for odds/payout
- ✅ Secondary bettors selection

### 3. **Backend Transformation** (`convert_ocr_to_bet_format()`)
```json
{
  "bet_id": "DK-12345678",
  "name": "3-Leg Parlay - DraftKings",
  "type": "parlay",
  "betting_site": "DraftKings",
  "bet_date": "2024-11-12",
  "wager": 20.00,
  "potential_winnings": 110.00,
  "final_odds": "+450",
  "legs": [
    {
      "bet_type": "player_prop",
      "bet_line_type": "over",
      ...
    }
  ]
}
```

### 4. **Database Write** (`save_bet_to_db()`)

**Bet Record (bets table):**
```sql
INSERT INTO bets (
  user_id,              -- from current_user.id
  bet_id,               -- from screenshot or generated
  bet_type,             -- from bet_data['type']
  betting_site,         -- from bet_data['betting_site']
  bet_date,             -- from bet_data['bet_date']
  wager,                -- from bet_data['wager']
  potential_winnings,   -- from bet_data['potential_winnings']
  final_odds,           -- from bet_data['final_odds'] (parsed as int)
  status,               -- calculated from legs
  total_legs,           -- count of legs
  legs_pending,         -- count where status='pending'
  bet_data,             -- full JSON
  secondary_bettors     -- array of user IDs
)
```

**BetLeg Records (bet_legs table):**
```sql
INSERT INTO bet_legs (
  bet_id,               -- FK to bets.id
  player_name,          -- from leg['player']
  player_team,          -- from leg['team']
  home_team,            -- from leg['home_team']
  away_team,            -- from leg['away_team']
  game_date,            -- from leg['game_date'] (date part)
  game_time,            -- from leg['game_date'] (time part)
  sport,                -- from leg['sport']
  bet_type,             -- from leg['bet_type']
  bet_line_type,        -- from leg['bet_line_type']
  target_value,         -- from leg['line']
  stat_type,            -- from leg['stat']
  final_leg_odds,       -- from leg['odds'] (parsed as int)
  status,               -- from leg['status']
  leg_order             -- from leg['leg_order']
)
```

---

## ✅ ALL REQUIREMENTS MET

| Requirement | Status |
|-------------|--------|
| `bet_id` from screenshot | ✅ **DONE** - Extracts from image, falls back to `ocr_xxxxxxxx` |
| `type` → `bets.bet_type` | ✅ **DONE** - Correctly mapped |
| `stake` → `bets.wager` | ✅ **DONE** - Field renamed to `wager` |
| `potential_return` → `bets.potential_winnings` | ✅ **DONE** - Field renamed to `potential_winnings` |
| `american_odds` → `bets.final_odds` | ✅ **DONE** - Field renamed to `final_odds` |
| Upload time → `bets.created_at` | ✅ **DONE** - Auto-populated by database |
| Leg `type` → `bet_legs.bet_type` | ✅ **DONE** - Correctly mapped |
| Leg `over_under` → `bet_legs.bet_line_type` | ✅ **DONE** - Field renamed to `bet_line_type` |

---

## 🎯 NEXT STEPS

### To Test:
1. Upload a bet slip with a visible bet ID (e.g., DraftKings confirmation number)
2. Verify bet_id is extracted from screenshot
3. Check database to confirm all fields are in correct columns:
   ```sql
   SELECT bet_id, bet_type, wager, potential_winnings, final_odds 
   FROM bets 
   WHERE bet_id LIKE 'DK-%' OR bet_id LIKE 'ocr_%';
   
   SELECT player_name, bet_type, bet_line_type, target_value 
   FROM bet_legs 
   WHERE bet_id = <bet_id>;
   ```

### Future Enhancements:
- **Player Matching**: Look up `player_id` from `players` table
- **Stats Integration**: Populate `player_season_avg`, `player_last_5_avg` from API
- **Live Updates**: Fill `game_status`, `current_quarter`, `time_remaining` from ESPN
- **Game IDs**: Match to ESPN `game_id` for better tracking
