-- Migration 001: Create New Schema
-- Purpose: Add structured tables for bets, bet_legs, players, and tax_data
-- Safe: Only adds new tables and columns, doesn't remove anything

-- =================================================================
-- 1. CREATE PLAYERS TABLE
-- =================================================================

CREATE TABLE IF NOT EXISTS players (
    id SERIAL PRIMARY KEY,
    
    -- Player Identity
    player_name VARCHAR(100) NOT NULL,
    normalized_name VARCHAR(100) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    
    -- Sport & Position
    sport VARCHAR(50) NOT NULL,
    position VARCHAR(20),
    position_group VARCHAR(20),
    jersey_number INTEGER,
    
    -- Team Information
    current_team VARCHAR(50),
    team_abbreviation VARCHAR(10),
    previous_teams TEXT,
    
    -- Physical Attributes
    height_inches INTEGER,
    weight_pounds INTEGER,
    birth_date DATE,
    age INTEGER,
    
    -- Career Status
    status VARCHAR(20) DEFAULT 'active',
    injury_status VARCHAR(100),
    contract_status VARCHAR(50),
    
    -- Season Statistics
    current_season VARCHAR(10),
    games_played INTEGER DEFAULT 0,
    games_started INTEGER DEFAULT 0,
    
    -- Performance Averages (JSON for flexibility)
    season_stats JSONB,
    last_5_games_stats JSONB,
    career_stats JSONB,
    
    -- Quick Access Stats (no JSON parsing)
    stat_category_1 VARCHAR(50),
    stat_value_1 DECIMAL(10, 2),
    stat_category_2 VARCHAR(50),
    stat_value_2 DECIMAL(10, 2),
    stat_category_3 VARCHAR(50),
    stat_value_3 DECIMAL(10, 2),
    
    -- API Integration
    espn_player_id VARCHAR(50),
    sports_reference_id VARCHAR(50),
    api_data_url TEXT,
    last_stats_update TIMESTAMP,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    data_source VARCHAR(50)
);

-- Indexes for players
CREATE UNIQUE INDEX IF NOT EXISTS idx_players_normalized_name_sport ON players(normalized_name, sport);
CREATE INDEX IF NOT EXISTS idx_players_current_team ON players(current_team);
CREATE INDEX IF NOT EXISTS idx_players_sport_position ON players(sport, position);
CREATE INDEX IF NOT EXISTS idx_players_name ON players(player_name);
CREATE INDEX IF NOT EXISTS idx_players_status ON players(status);

-- =================================================================
-- 2. ADD NEW COLUMNS TO BETS TABLE
-- =================================================================

-- Financial columns
ALTER TABLE bets ADD COLUMN IF NOT EXISTS wager DECIMAL(10, 2);
ALTER TABLE bets ADD COLUMN IF NOT EXISTS original_odds INTEGER;
ALTER TABLE bets ADD COLUMN IF NOT EXISTS boosted_odds INTEGER;
ALTER TABLE bets ADD COLUMN IF NOT EXISTS final_odds INTEGER;
ALTER TABLE bets ADD COLUMN IF NOT EXISTS is_boosted BOOLEAN DEFAULT FALSE;
ALTER TABLE bets ADD COLUMN IF NOT EXISTS potential_winnings DECIMAL(10, 2);
ALTER TABLE bets ADD COLUMN IF NOT EXISTS actual_winnings DECIMAL(10, 2);

-- Parlay insurance columns
ALTER TABLE bets ADD COLUMN IF NOT EXISTS has_insurance BOOLEAN DEFAULT FALSE;
ALTER TABLE bets ADD COLUMN IF NOT EXISTS insurance_type VARCHAR(50);
ALTER TABLE bets ADD COLUMN IF NOT EXISTS insurance_amount DECIMAL(10, 2);
ALTER TABLE bets ADD COLUMN IF NOT EXISTS insurance_triggered BOOLEAN DEFAULT FALSE;

-- Bet statistics columns
ALTER TABLE bets ADD COLUMN IF NOT EXISTS total_legs INTEGER DEFAULT 0;
ALTER TABLE bets ADD COLUMN IF NOT EXISTS legs_won INTEGER DEFAULT 0;
ALTER TABLE bets ADD COLUMN IF NOT EXISTS legs_lost INTEGER DEFAULT 0;
ALTER TABLE bets ADD COLUMN IF NOT EXISTS legs_pending INTEGER DEFAULT 0;
ALTER TABLE bets ADD COLUMN IF NOT EXISTS legs_live INTEGER DEFAULT 0;
ALTER TABLE bets ADD COLUMN IF NOT EXISTS legs_void INTEGER DEFAULT 0;

-- API tracking
ALTER TABLE bets ADD COLUMN IF NOT EXISTS last_api_update TIMESTAMP;

-- Create indexes on new columns
CREATE INDEX IF NOT EXISTS idx_bets_boosted ON bets(is_boosted);
CREATE INDEX IF NOT EXISTS idx_bets_insurance ON bets(has_insurance);
CREATE INDEX IF NOT EXISTS idx_bets_final_odds ON bets(final_odds);

-- =================================================================
-- 3. CREATE BET_LEGS TABLE
-- =================================================================

CREATE TABLE IF NOT EXISTS bet_legs (
    id SERIAL PRIMARY KEY,
    bet_id INTEGER NOT NULL REFERENCES bets(id) ON DELETE CASCADE,
    player_id INTEGER REFERENCES players(id),
    
    -- Player/Team Info (denormalized for performance)
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
    sport VARCHAR(50),
    parlay_sport VARCHAR(50),
    
    -- Bet Details
    bet_type VARCHAR(50) NOT NULL,
    bet_line_type VARCHAR(20),
    target_value DECIMAL(10, 2) NOT NULL,
    achieved_value DECIMAL(10, 2),
    stat_type VARCHAR(20),
    
    -- Performance Comparison
    player_season_avg DECIMAL(10, 2),
    player_last_5_avg DECIMAL(10, 2),
    vs_opponent_avg DECIMAL(10, 2),
    target_vs_season DECIMAL(10, 2),
    
    -- Odds Tracking
    original_leg_odds INTEGER,
    boosted_leg_odds INTEGER,
    final_leg_odds INTEGER,
    
    -- Leg Status
    status VARCHAR(20) DEFAULT 'pending',
    is_hit BOOLEAN,
    void_reason VARCHAR(100),
    
    -- Live Game Data
    current_quarter VARCHAR(10),
    time_remaining VARCHAR(20),
    home_score INTEGER,
    away_score INTEGER,
    
    -- Contextual Data
    is_home_game BOOLEAN,
    weather_conditions VARCHAR(100),
    injury_during_game BOOLEAN DEFAULT FALSE,
    dnp_reason VARCHAR(100),
    
    -- Metadata
    leg_order INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for bet_legs
CREATE INDEX IF NOT EXISTS idx_bet_legs_bet_id ON bet_legs(bet_id);
CREATE INDEX IF NOT EXISTS idx_bet_legs_player_id ON bet_legs(player_id);
CREATE INDEX IF NOT EXISTS idx_bet_legs_player_name ON bet_legs(player_name);
CREATE INDEX IF NOT EXISTS idx_bet_legs_game_id ON bet_legs(game_id);
CREATE INDEX IF NOT EXISTS idx_bet_legs_bet_type ON bet_legs(bet_type);
CREATE INDEX IF NOT EXISTS idx_bet_legs_status ON bet_legs(status);
CREATE INDEX IF NOT EXISTS idx_bet_legs_sport ON bet_legs(sport);
CREATE INDEX IF NOT EXISTS idx_bet_legs_parlay_sport ON bet_legs(parlay_sport);

-- =================================================================
-- 4. CREATE TAX_DATA TABLE
-- =================================================================

CREATE TABLE IF NOT EXISTS tax_data (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    
    -- Tax Year
    tax_year INTEGER NOT NULL,
    
    -- Financial Summary
    total_wagered DECIMAL(10, 2) DEFAULT 0,
    total_winnings DECIMAL(10, 2) DEFAULT 0,
    net_profit DECIMAL(10, 2) DEFAULT 0,
    
    -- Bet Counts
    total_bets INTEGER DEFAULT 0,
    winning_bets INTEGER DEFAULT 0,
    losing_bets INTEGER DEFAULT 0,
    
    -- Breakdown by site and month
    site_breakdown JSONB,
    monthly_summary JSONB,
    
    -- Metadata
    last_calculated TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT unique_user_year UNIQUE (user_id, tax_year)
);

-- Indexes for tax_data
CREATE INDEX IF NOT EXISTS idx_tax_data_user_year ON tax_data(user_id, tax_year);

-- =================================================================
-- 5. CREATE PLAYER_PERFORMANCE_CACHE TABLE (OPTIONAL)
-- =================================================================

CREATE TABLE IF NOT EXISTS player_performance_cache (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id),
    
    -- Cache Key
    stat_type VARCHAR(50) NOT NULL,
    opponent_team VARCHAR(50),
    season VARCHAR(10) NOT NULL,
    
    -- Cached Value
    stat_value DECIMAL(10, 2) NOT NULL,
    games_sample INTEGER,
    
    -- Cache Management
    cached_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    
    CONSTRAINT unique_cache_key UNIQUE (player_id, stat_type, opponent_team, season)
);

-- Indexes for performance cache
CREATE INDEX IF NOT EXISTS idx_cache_player_stat ON player_performance_cache(player_id, stat_type);
CREATE INDEX IF NOT EXISTS idx_cache_expires ON player_performance_cache(expires_at);

-- =================================================================
-- MIGRATION COMPLETE
-- =================================================================

-- Add migration tracking
CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(100) UNIQUE NOT NULL,
    applied_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO schema_migrations (migration_name) 
VALUES ('001_create_new_schema')
ON CONFLICT (migration_name) DO NOTHING;
