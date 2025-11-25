-- Create Audit Logging Tables
-- Run this script to create the audit logging tables for tracking changes and validation results

-- Table 1: General Audit Log
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW() NOT NULL,
    
    -- What happened
    event_type VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
    
    -- Who/What did it
    actor_type VARCHAR(50) NOT NULL,  -- 'automation', 'user', 'system'
    actor_name VARCHAR(100) NOT NULL,
    
    -- What was affected
    entity_type VARCHAR(50) NOT NULL,  -- 'bet', 'bet_leg', 'user'
    entity_id INTEGER,
    
    -- Details
    old_value TEXT,
    new_value TEXT,
    metadata JSONB,
    
    -- Result
    success BOOLEAN DEFAULT TRUE NOT NULL,
    error_message TEXT
);

-- Indexes for audit_log
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_event ON audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_log(actor_type, actor_name);

-- Table 2: Data Validation Log
CREATE TABLE IF NOT EXISTS data_validation_log (
    id SERIAL PRIMARY KEY,
    validation_run_id UUID NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW() NOT NULL,
    
    -- What was checked
    bet_id INTEGER,
    bet_leg_id INTEGER,
    player_name VARCHAR(100),
    stat_type VARCHAR(50),
    
    -- Issue details
    issue_type VARCHAR(50) NOT NULL,  -- 'value_mismatch', 'game_id_issue', 'missing_game_id'
    stored_value NUMERIC(10, 2),
    espn_value NUMERIC(10, 2),
    difference NUMERIC(10, 2),
    
    -- Game info
    game_id VARCHAR(50),
    game_date DATE,
    teams VARCHAR(200),
    
    -- Details
    details JSONB,
    
    -- Resolution
    resolved BOOLEAN DEFAULT FALSE NOT NULL,
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(100),
    resolution_notes TEXT
);

-- Indexes for data_validation_log
CREATE INDEX IF NOT EXISTS idx_validation_unresolved ON data_validation_log(resolved) WHERE resolved = FALSE;
CREATE INDEX IF NOT EXISTS idx_validation_bet ON data_validation_log(bet_id, bet_leg_id);
CREATE INDEX IF NOT EXISTS idx_validation_run ON data_validation_log(validation_run_id);
CREATE INDEX IF NOT EXISTS idx_validation_timestamp ON data_validation_log(timestamp);

-- Table 3: Automation Runs
CREATE TABLE IF NOT EXISTS automation_runs (
    id SERIAL PRIMARY KEY,
    automation_name VARCHAR(100) NOT NULL,
    started_at TIMESTAMP DEFAULT NOW() NOT NULL,
    completed_at TIMESTAMP,
    duration_seconds NUMERIC(10, 2),
    
    -- Results
    success_count INTEGER DEFAULT 0 NOT NULL,
    failure_count INTEGER DEFAULT 0 NOT NULL,
    skipped_count INTEGER DEFAULT 0 NOT NULL,
    
    -- Status
    status VARCHAR(20) NOT NULL,  -- 'success', 'partial_failure', 'failed', 'running'
    error_message TEXT,
    
    -- Metadata
    processed_items JSONB
);

-- Indexes for automation_runs
CREATE INDEX IF NOT EXISTS idx_automation_name ON automation_runs(automation_name);
CREATE INDEX IF NOT EXISTS idx_automation_recent ON automation_runs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_automation_status ON automation_runs(status);

-- Grant permissions (adjust if needed for your database user)
-- GRANT SELECT, INSERT, UPDATE ON audit_log TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE ON data_validation_log TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE ON automation_runs TO your_app_user;
