# Enhanced Database Schema - Final Design

## Complete Schema with Players Table

### 1. **players** table (NEW)
**Purpose**: Central repository for all player information across sports

```sql
CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    
    -- Player Identity
    player_name VARCHAR(100) NOT NULL,
    normalized_name VARCHAR(100) NOT NULL,    -- "patrick mahomes" for matching
    display_name VARCHAR(100) NOT NULL,        -- "Patrick Mahomes II"
    
    -- Sport & Position
    sport VARCHAR(50) NOT NULL,                -- 'NFL', 'NBA', 'MLB', 'NHL', 'NCAAF', 'NCAAB', 'Soccer'
    position VARCHAR(20),                      -- QB, RB, WR, TE, K, PG, SG, SF, PF, C, P, SP, RP, etc.
    position_group VARCHAR(20),                -- 'Offense', 'Defense', 'Special Teams', 'Forward', 'Guard'
    jersey_number INTEGER,
    
    -- Team Information
    current_team VARCHAR(50),                  -- "Kansas City Chiefs"
    team_abbreviation VARCHAR(10),             -- "KC", "LAL", "NYY"
    previous_teams TEXT,                       -- JSON array of previous teams
    
    -- Physical Attributes
    height_inches INTEGER,                     -- Total inches (6'2" = 74)
    weight_pounds INTEGER,
    birth_date DATE,
    age INTEGER,
    
    -- Career Status
    status VARCHAR(20) DEFAULT 'active',       -- 'active', 'injured', 'suspended', 'retired', 'free_agent'
    injury_status VARCHAR(100),                -- "Questionable - Ankle", "Out - Concussion"
    contract_status VARCHAR(50),               -- 'signed', 'franchise_tag', 'unsigned'
    
    -- Season Statistics (Current Season)
    current_season VARCHAR(10),                -- "2024-2025", "2024"
    games_played INTEGER DEFAULT 0,
    games_started INTEGER DEFAULT 0,
    
    -- Performance Averages (Sport-Specific stored as JSON)
    season_stats JSONB,                        -- Current season detailed stats
    last_5_games_stats JSONB,                  -- Last 5 games averages
    career_stats JSONB,                        -- Career totals/averages
    
    -- Common Stats Across Sports (for quick access without JSON parsing)
    -- NFL: passing_yards, rushing_yards, receiving_yards, touchdowns, receptions
    stat_category_1 VARCHAR(50),               -- e.g., "passing_yards"
    stat_value_1 DECIMAL(10, 2),              -- e.g., 287.5 (season avg)
    stat_category_2 VARCHAR(50),               -- e.g., "touchdowns"
    stat_value_2 DECIMAL(10, 2),              -- e.g., 2.1 (season avg)
    stat_category_3 VARCHAR(50),               -- e.g., "completion_percentage"
    stat_value_3 DECIMAL(10, 2),              -- e.g., 67.8
    
    -- External API Integration
    espn_player_id VARCHAR(50),                -- ESPN API ID
    sports_reference_id VARCHAR(50),           -- Sports Reference ID
    api_data_url TEXT,                         -- Direct URL to fetch latest stats
    last_stats_update TIMESTAMP,               -- Last time we fetched stats
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    data_source VARCHAR(50),                   -- 'espn', 'manual', 'nfl_api', etc.
    
    -- Indexes
    UNIQUE INDEX idx_normalized_name_sport (normalized_name, sport),
    INDEX idx_current_team (current_team),
    INDEX idx_sport_position (sport, position),
    INDEX idx_player_name (player_name),
    INDEX idx_status (status)
);
```

**Sport-Specific Stats Examples:**

**NFL (in season_stats JSONB):**
```json
{
  "passing": {"yards": 4248, "tds": 31, "ints": 9, "rating": 103.2},
  "rushing": {"yards": 156, "tds": 2, "avg": 3.9},
  "receiving": {"receptions": 0, "yards": 0, "tds": 0}
}
```

**NBA:**
```json
{
  "scoring": {"ppg": 27.3, "fg_pct": 48.2, "3pt_pct": 37.1, "ft_pct": 88.9},
  "playmaking": {"apg": 6.2, "topg": 2.8},
  "rebounding": {"rpg": 8.1, "orpg": 1.2, "drpg": 6.9},
  "defense": {"spg": 1.4, "bpg": 0.6}
}
```

**MLB:**
```json
{
  "batting": {"avg": 0.298, "hr": 28, "rbi": 92, "ops": 0.867},
  "pitching": {"era": 3.42, "wins": 12, "strikeouts": 187, "whip": 1.18}
}
```

---

### 2. **bets** table (Enhanced)

```sql
CREATE TABLE bets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    
    -- Bet Identity
    bet_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200),
    bet_type VARCHAR(50),                      -- 'Parlay', 'SGP', 'Single'
    betting_site VARCHAR(50),
    bet_date DATE NOT NULL,
    
    -- Bet Financials
    wager DECIMAL(10, 2) NOT NULL,
    original_odds INTEGER,                     -- NEW: Odds before boost
    boosted_odds INTEGER,                      -- NEW: Odds after boost
    final_odds INTEGER NOT NULL,               -- Actual odds used
    is_boosted BOOLEAN DEFAULT FALSE,          -- NEW: Was boost applied
    potential_winnings DECIMAL(10, 2),
    actual_winnings DECIMAL(10, 2),
    
    -- Parlay Insurance (NEW)
    has_insurance BOOLEAN DEFAULT FALSE,       -- NEW: Has 1-leg insurance
    insurance_type VARCHAR(50),                -- NEW: 'one_leg_back', 'percentage_back'
    insurance_amount DECIMAL(10, 2),          -- NEW: Refund amount if triggered
    insurance_triggered BOOLEAN DEFAULT FALSE, -- NEW: Was insurance used
    
    -- Bet Statistics
    total_legs INTEGER NOT NULL DEFAULT 0,
    legs_won INTEGER NOT NULL DEFAULT 0,
    legs_lost INTEGER NOT NULL DEFAULT 0,
    legs_pending INTEGER NOT NULL DEFAULT 0,
    legs_live INTEGER NOT NULL DEFAULT 0,
    legs_void INTEGER NOT NULL DEFAULT 0,     -- NEW: Voided legs
    
    -- Bet Status
    status VARCHAR(20) DEFAULT 'pending',
    is_active BOOLEAN DEFAULT TRUE,
    is_archived BOOLEAN DEFAULT FALSE,
    
    -- API Integration
    api_fetched BOOLEAN DEFAULT FALSE,
    last_api_update TIMESTAMP,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_user_status (user_id, status),
    INDEX idx_bet_date (bet_date DESC),
    INDEX idx_betting_site (betting_site),
    INDEX idx_status_active (status, is_active),
    INDEX idx_boosted (is_boosted),           -- NEW: Find boosted bets
    INDEX idx_insurance (has_insurance)       -- NEW: Find insured bets
);
```

---

### 3. **bet_legs** table (Enhanced)

```sql
CREATE TABLE bet_legs (
    id SERIAL PRIMARY KEY,
    bet_id INTEGER NOT NULL REFERENCES bets(id) ON DELETE CASCADE,
    player_id INTEGER REFERENCES players(id),  -- NEW: Link to players table
    
    -- Player/Team Info (Denormalized for performance)
    player_name VARCHAR(100) NOT NULL,
    player_team VARCHAR(50),
    player_position VARCHAR(10),
    
    -- Game Info
    home_team VARCHAR(50) NOT NULL,
    away_team VARCHAR(50) NOT NULL,
    game_id VARCHAR(50),
    game_date DATE,
    game_time TIME,
    game_status VARCHAR(20),
    sport VARCHAR(50),                         -- NEW: Sport type (from game)
    parlay_sport VARCHAR(50),                  -- NEW: Parlay category (NBA, NFL, MLB, etc.)
    
    -- Bet Details
    bet_type VARCHAR(50) NOT NULL,
    bet_line_type VARCHAR(20),                 -- 'over', 'under', NULL
    target_value DECIMAL(10, 2) NOT NULL,
    achieved_value DECIMAL(10, 2),
    stat_type VARCHAR(20),
    
    -- Performance Comparison (NEW)
    player_season_avg DECIMAL(10, 2),          -- NEW: Player's season average
    player_last_5_avg DECIMAL(10, 2),          -- NEW: Last 5 games average
    vs_opponent_avg DECIMAL(10, 2),            -- NEW: Historical vs opponent
    target_vs_season DECIMAL(10, 2),           -- NEW: % above/below season avg
    
    -- Odds Tracking (NEW)
    original_leg_odds INTEGER,                 -- NEW: Original odds for this leg
    boosted_leg_odds INTEGER,                  -- NEW: Boosted odds if applicable
    final_leg_odds INTEGER,                    -- NEW: Actual odds
    
    -- Leg Status
    status VARCHAR(20) DEFAULT 'pending',
    is_hit BOOLEAN,
    void_reason VARCHAR(100),                  -- NEW: Reason if voided
    
    -- Live Game Data
    current_quarter VARCHAR(10),
    time_remaining VARCHAR(20),
    home_score INTEGER,
    away_score INTEGER,
    
    -- Contextual Data (NEW)
    is_home_game BOOLEAN,                      -- NEW: Is player's team home
    weather_conditions VARCHAR(100),           -- NEW: For outdoor sports
    injury_during_game BOOLEAN DEFAULT FALSE,  -- NEW: Injured mid-game
    dnp_reason VARCHAR(100),                   -- NEW: Did Not Play reason
    
    -- Metadata
    leg_order INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_bet_id (bet_id),
    INDEX idx_player_id (player_id),          -- NEW: Query by player
    INDEX idx_player_name (player_name),
    INDEX idx_game_id (game_id),
    INDEX idx_bet_type (bet_type),
    INDEX idx_status (status),
    INDEX idx_sport (sport)                   -- NEW: Filter by sport
);
```

---

### 4. **tax_data** table (NEW - Backend Only)
**Purpose**: Track yearly profit/loss for tax reporting

```sql
CREATE TABLE tax_data (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    
    -- Tax Year
    tax_year INTEGER NOT NULL,                 -- 2024, 2025
    
    -- Financial Summary
    total_wagered DECIMAL(10, 2) DEFAULT 0,
    total_winnings DECIMAL(10, 2) DEFAULT 0,
    net_profit DECIMAL(10, 2) DEFAULT 0,       -- winnings - wagered
    
    -- Bet Counts
    total_bets INTEGER DEFAULT 0,
    winning_bets INTEGER DEFAULT 0,
    losing_bets INTEGER DEFAULT 0,
    
    -- By Betting Site
    site_breakdown JSONB,                      -- {"FanDuel": {"wagered": 500, "winnings": 650}, ...}
    
    -- Monthly Breakdown
    monthly_summary JSONB,                     -- {"2024-01": {"profit": 125.50}, ...}
    
    -- Metadata
    last_calculated TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    UNIQUE (user_id, tax_year),
    INDEX idx_user_year (user_id, tax_year)
);
```

---

### 5. **player_performance_cache** table (NEW - Optional)
**Purpose**: Cache player stats to reduce API calls

```sql
CREATE TABLE player_performance_cache (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id),
    
    -- Cache Key
    stat_type VARCHAR(50) NOT NULL,            -- 'season_avg', 'last_5', 'vs_opponent'
    opponent_team VARCHAR(50),                 -- NULL if not opponent-specific
    season VARCHAR(10) NOT NULL,               -- "2024-2025"
    
    -- Cached Value
    stat_value DECIMAL(10, 2) NOT NULL,
    games_sample INTEGER,                      -- How many games in average
    
    -- Cache Management
    cached_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,                      -- When to refresh
    
    -- Constraints
    UNIQUE (player_id, stat_type, opponent_team, season),
    INDEX idx_player_stat (player_id, stat_type),
    INDEX idx_expires (expires_at)
);
```

---

## Sport-Specific Position Mappings

### NFL
- **Offense**: QB, RB, WR, TE, OL (C, G, T)
- **Defense**: DL (DE, DT), LB, DB (CB, S)
- **Special Teams**: K, P, LS, KR, PR

### NBA
- **Positions**: PG, SG, SF, PF, C
- **Position Groups**: Guard, Forward, Center

### MLB
- **Pitching**: SP (Starting Pitcher), RP (Relief Pitcher), CP (Closer)
- **Position Players**: C, 1B, 2B, 3B, SS, LF, CF, RF, DH

### NHL
- **Positions**: C (Center), LW, RW, D (Defenseman), G (Goalie)

### Soccer
- **Positions**: GK, LB, CB, RB, LM, CM, RM, LW, ST, RW

---

## Migration Plan

### Step 1: Create New Tables (30 min)
```sql
-- Run in order:
1. CREATE TABLE players
2. CREATE TABLE tax_data
3. CREATE TABLE player_performance_cache
4. ALTER TABLE bets (add new columns)
5. ALTER TABLE bet_legs (add new columns)
```

### Step 2: Migrate Existing Data (2-3 hours)
1. Parse JSON from existing `bet_data`
2. Extract bet-level info → populate new `bets` columns
3. Extract legs → create `bet_legs` records
4. Create `players` records from unique players in legs
5. Link `bet_legs.player_id` to `players.id`
6. Calculate tax_data for each user/year

### Step 3: Update Application Code (3-4 hours)
1. Create new SQLAlchemy models
2. Update API endpoints
3. Add player stats fetching service
4. Update frontend to use structured data

### Step 4: Testing (2 hours)
1. Test locally with sample data
2. Verify all relationships
3. Test API endpoints
4. Test frontend display

---

## New Features Enabled

### 1. Player Analytics Dashboard
```sql
-- Find most profitable players to bet on
SELECT p.player_name, p.position, 
       COUNT(*) as total_bets,
       SUM(CASE WHEN bl.is_hit THEN 1 ELSE 0 END) as hits,
       ROUND(SUM(CASE WHEN bl.is_hit THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 1) as hit_rate
FROM bet_legs bl
JOIN players p ON bl.player_id = p.id
GROUP BY p.player_name, p.position
HAVING COUNT(*) >= 5
ORDER BY hit_rate DESC;
```

### 2. Odds Boost Analysis
```sql
-- Compare boosted vs non-boosted bet performance
SELECT 
    CASE WHEN is_boosted THEN 'Boosted' ELSE 'Regular' END as bet_type,
    COUNT(*) as total_bets,
    SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END) as wins,
    ROUND(AVG(final_odds), 0) as avg_odds,
    SUM(actual_winnings - wager) as profit
FROM bets
GROUP BY is_boosted;
```

### 3. Tax Report Generation
```sql
-- Generate annual tax summary
SELECT 
    tax_year,
    total_wagered,
    total_winnings,
    net_profit,
    total_bets,
    ROUND(winning_bets::numeric / total_bets * 100, 1) as win_rate
FROM tax_data
WHERE user_id = :user_id
ORDER BY tax_year DESC;
```

---

## Next Steps

1. **Review this enhanced design** - Any changes needed?
2. **I'll create migration scripts** - Safe, reversible migrations
3. **Test locally** - Migrate your local SQLite
4. **Backup production** - Before touching Render
5. **Run production migration** - With monitoring
6. **Update code** - Models, API, frontend
7. **Deploy** - Roll out new features

**Ready to proceed?** This will take about 1-2 days total but will give you a professional-grade analytics platform!
