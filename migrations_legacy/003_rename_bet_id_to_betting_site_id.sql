-- Migration 003: Rename bet_id to betting_site_id in bets table
-- Purpose: Rename confusing column name to clarify that it refers to betting site ID, not bet ID
-- Safe: Only renames a column, preserves all data

-- Rename the column in the bets table
ALTER TABLE bets RENAME COLUMN bet_id TO betting_site_id;

-- Update any indexes that reference the old column name (if they exist)
-- Note: The column has an index but we don't need to recreate it as PostgreSQL handles this automatically