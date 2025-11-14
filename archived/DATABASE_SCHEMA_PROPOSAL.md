# Database Schema Redesign Proposal

## Current Issues
1. **Bet data stored as JSON blob** - Makes querying, filtering, and reporting difficult
2. **No leg-level tracking** - Can't analyze individual leg performance
3. **Missing bet-level fields** - Odds, wager, winnings not in structured columns
4. **No historical analytics** - Can't easily answer "Which player props win most?"

## Proposed Schema

### 1. **bets** table (Enhanced)
**Purpose**: Store bet-level information

```sql
CREATE TABLE bets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    
    -- Bet Identity
    bet_id VARCHAR(100) UNIQUE NOT NULL,  -- External ID from betting site
    name VARCHAR(200),                     -- "7 Pick Parlay", "Lamar Jackson SGP"
    bet_type VARCHAR(50),                  -- 'Parlay', 'SGP', 'Single'
    betting_site VARCHAR(50),              -- 'FanDuel', 'DraftKings', 'Dabble'
    bet_date DATE NOT NULL,                -- When bet was placed
    
    -- Bet Financials (NEW)
    wager DECIMAL(10, 2) NOT NULL,        -- Amount wagered ($10.00)
    odds INTEGER NOT NULL,                 -- American odds (+650, -110)
    potential_winnings DECIMAL(10, 2),    -- Calculated: wager * odds
    actual_winnings DECIMAL(10, 2),       -- NULL if pending/lost, amount if won
    
    -- Bet Statistics (NEW)
    total_legs INTEGER NOT NULL DEFAULT 0,
    legs_won INTEGER NOT NULL DEFAULT 0,
    legs_lost INTEGER NOT NULL DEFAULT 0,
    legs_pending INTEGER NOT NULL DEFAULT 0,
    legs_live INTEGER NOT NULL DEFAULT 0,
    
    -- Bet Status
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'live', 'won', 'lost'
    is_active BOOLEAN DEFAULT TRUE,        -- Live/active vs historical
    is_archived BOOLEAN DEFAULT FALSE,     -- User archived
    
    -- API Integration
    api_fetched BOOLEAN DEFAULT FALSE,     -- ESPN data fetched
    last_api_update TIMESTAMP,             -- Last time we fetched live data
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_user_status (user_id, status),
    INDEX idx_bet_date (bet_date DESC),
    INDEX idx_betting_site (betting_site),
    INDEX idx_status_active (status, is_active)
);
```

**NEW COLUMNS:**
- `wager` - Amount bet
- `odds` - American odds format
- `potential_winnings` - Calculated payout
- `actual_winnings` - Real winnings if won
- `total_legs` - Total number of legs
- `legs_won/lost/pending/live` - Leg status counts
- `last_api_update` - Track API freshness

---

### 2. **bet_legs** table (NEW)
**Purpose**: Store individual parlay legs

```sql
CREATE TABLE bet_legs (
    id SERIAL PRIMARY KEY,
    bet_id INTEGER NOT NULL REFERENCES bets(id) ON DELETE CASCADE,
    
    -- Player/Team Info
    player_name VARCHAR(100) NOT NULL,
    player_team VARCHAR(50),              -- Team player is on
    player_position VARCHAR(10),          -- QB, RB, WR, TE, etc.
    
    -- Game Info
    home_team VARCHAR(50) NOT NULL,
    away_team VARCHAR(50) NOT NULL,
    game_id VARCHAR(50),                  -- ESPN game ID for live data
    game_date DATE,
    game_time TIME,
    game_status VARCHAR(20),              -- 'scheduled', 'live', 'final'
    
    -- Bet Details
    bet_type VARCHAR(50) NOT NULL,        -- 'Passing Yards', 'Rushing Yards', 'Receptions', 
                                          -- 'Touchdowns', 'Moneyline', 'Spread', 'Points'
    bet_line_type VARCHAR(20),            -- 'over', 'under', NULL for moneyline
    target_value DECIMAL(10, 2) NOT NULL, -- Target stat (e.g., 249.5 yards, 7.5 points)
    achieved_value DECIMAL(10, 2),        -- Actual stat achieved (live updates)
    stat_type VARCHAR(20),                -- 'yards', 'points', 'receptions', 'touchdowns'
    
    -- Leg Status
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'live', 'won', 'lost'
    is_hit BOOLEAN,                       -- TRUE if won, FALSE if lost, NULL if pending
    
    -- Live Game Data (for progress tracking)
    current_quarter VARCHAR(10),          -- 'Q1', 'Q2', 'Q3', 'Q4', 'OT', 'Final'
    time_remaining VARCHAR(20),           -- "14:32", "Final"
    home_score INTEGER,
    away_score INTEGER,
    
    -- Metadata
    leg_order INTEGER,                    -- Order in parlay (1, 2, 3...)
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_bet_id (bet_id),
    INDEX idx_player_name (player_name),
    INDEX idx_game_id (game_id),
    INDEX idx_bet_type (bet_type),
    INDEX idx_status (status)
);
```

**KEY FEATURES:**
- Complete player/team/game information
- Bet line details (over/under, target)
- Live stat tracking
- Game status and scores
- Ordered legs for display

---

### 3. **bet_users** table (Keep existing)
**Purpose**: Many-to-many relationship for shared bets

```sql
-- Already exists, no changes needed
CREATE TABLE bet_users (
    bet_id INTEGER REFERENCES bets(id),
    user_id INTEGER REFERENCES users(id),
    is_primary_bettor BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (bet_id, user_id)
);
```

---

## Additional Fields to Track

### In **bet_legs** table, consider adding:

1. **opponent_team** - Team playing against player's team
2. **is_home_game** - Boolean if player's team is home
3. **weather_conditions** - For outdoor games (future enhancement)
4. **odds_per_leg** - Individual leg odds if available
5. **injury_status** - Track if player was injured mid-game
6. **dnp_reason** - "Did Not Play" reason if applicable
7. **substituted** - If bet was affected by player substitution
8. **voided** - If leg was voided by sportsbook

### Analytics Fields (Optional):
```sql
-- Player performance history
player_season_avg DECIMAL(10, 2),     -- Season average for this stat
player_last_5_avg DECIMAL(10, 2),     -- Last 5 games average
vs_opponent_history DECIMAL(10, 2),   -- Historical vs this opponent

-- Bet context
is_boosted BOOLEAN,                   -- Odds boost applied
original_odds INTEGER,                -- Pre-boost odds
parlay_insurance BOOLEAN,             -- Has "parlay insurance" feature
```

---

## Migration Strategy

### Phase 1: Add New Tables (Non-breaking)
1. Create `bet_legs` table
2. Add new columns to `bets` table (all nullable initially)
3. Keep `bet_data` JSON column temporarily

### Phase 2: Data Migration Script
1. Parse existing JSON blobs
2. Extract bet-level fields → populate new `bets` columns
3. Extract legs → create `bet_legs` records
4. Verify data integrity
5. Update all foreign keys and relationships

### Phase 3: Update Application Code
1. Modify models.py with new schema
2. Update API endpoints to read from structured tables
3. Update frontend to work with new API structure
4. Test thoroughly

### Phase 4: Deprecate JSON (Future)
1. Once stable, remove `bet_data` column
2. Remove JSON parsing code
3. Optimize queries with new structure

---

## Benefits of New Schema

### 1. **Querying & Analytics**
```sql
-- Find best performing bet types
SELECT bet_type, COUNT(*), AVG(achieved_value/target_value)
FROM bet_legs 
WHERE status = 'won'
GROUP BY bet_type;

-- Player performance tracking
SELECT player_name, COUNT(*) as total_bets, 
       SUM(CASE WHEN is_hit THEN 1 ELSE 0 END) as wins
FROM bet_legs
GROUP BY player_name
ORDER BY total_bets DESC;

-- Find most profitable sites
SELECT betting_site, SUM(actual_winnings - wager) as profit
FROM bets
WHERE status = 'won'
GROUP BY betting_site;
```

### 2. **Frontend Benefits**
- Direct SQL queries (faster than JSON parsing)
- Easy filtering/sorting
- Real-time leg-by-leg updates
- Better data validation

### 3. **Reporting**
- Win rate by bet type
- Player prop success rates
- Site comparison
- Date range analysis
- Leg performance trends

### 4. **Data Integrity**
- Foreign key constraints
- NOT NULL enforcement
- Type checking at DB level
- Cascade deletes

---

## Questions for You

1. **Do you want to track parlay insurance?** (Some sites refund if only 1 leg loses)

2. **Should we track odds boosts separately?** (Original odds vs boosted)

3. **Do you want player season averages?** (Requires integration with stats API)

4. **Archive strategy?** Should old bet_legs be moved to archive table after X months?

5. **Multi-currency support?** Or always USD?

6. **Tax reporting?** Track net profit per year automatically?

7. **Leg-level notes?** Allow users to add comments per leg? ("Bad weather", "Injury")

---

## Estimated Migration Time

- **Schema creation**: 30 minutes
- **Migration script**: 2-3 hours
- **Testing migration**: 1 hour
- **Code updates**: 3-4 hours
- **Frontend updates**: 2-3 hours
- **Testing everything**: 2 hours

**Total**: 1-2 days of development

---

## Next Steps

1. Review this proposal
2. Answer questions above
3. I'll create migration scripts
4. Test locally first
5. Run on production with backup

**Ready to proceed?** Let me know what you think and any changes you'd like!
