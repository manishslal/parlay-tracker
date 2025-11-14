# Database Migration Guide

## Overview
This migration adds structured tables for bets, bet legs, players, and tax data, replacing the JSON blob storage with proper relational database structure.

## What's Being Added

### New Tables
1. **players** - Central player repository with stats and info
2. **bet_legs** - Individual parlay legs with detailed tracking
3. **tax_data** - Yearly profit/loss tracking
4. **player_performance_cache** - Cached stats for performance

### Enhanced Tables
- **bets** - Added 15+ new columns for wager, odds, winnings, insurance, leg counts

## Migration Files

### 1. `001_create_new_schema.sql`
- Creates all new tables
- Adds new columns to existing bets table
- Creates indexes for performance
- **Safe**: Only adds, doesn't remove anything

### 2. `002_migrate_bet_data.py`
- Parses existing bet_data JSON
- Populates new structured tables
- Creates player records
- Calculates tax data
- **Safe**: Only reads and writes, doesn't delete

### 3. `run_migration.py` (Master Script)
- Checks database connection
- Creates backup
- Runs migrations in order
- Tracks applied migrations
- Reports results

## How to Run

### Local Testing (Recommended First)

```bash
# 1. Make sure you're using local SQLite
# No DATABASE_URL set = uses SQLite

# 2. Run migration
python3 run_migration.py

# 3. Verify data looks good
# Use pgAdmin or check tables directly
```

### Production (Render)

```bash
# 1. Get your DATABASE_URL from Render dashboard
export DATABASE_URL='postgresql://user:pass@host/db'

# 2. Run migration (creates backup automatically)
python3 run_migration.py

# 3. Verify on Render
# Check database in pgAdmin or Render dashboard
```

## Migration Steps

The script will:
1. ✅ Check database connection
2. ✅ Show what migrations will run
3. ❓ Ask for confirmation
4. 💾 Offer to create backup
5. 🔧 Run schema creation (001)
6. 📦 Run data migration (002)
7. ✅ Report success/failure

## Backup & Rollback

### Automatic Backup
The script asks if you want a backup before proceeding. **Always say yes for production!**

Backup file format: `backup_before_migration_YYYYMMDD_HHMMSS.sql`

### Manual Backup
```bash
pg_dump "$DATABASE_URL" > my_backup.sql
```

### Restore from Backup
```bash
psql "$DATABASE_URL" < my_backup.sql
```

## Verification After Migration

### Check Tables Were Created
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Should see: bet_legs, players, tax_data, player_performance_cache
```

### Check Bet Data Was Migrated
```sql
-- Check bets have new columns populated
SELECT bet_id, wager, final_odds, total_legs, legs_won, legs_lost
FROM bets
WHERE wager IS NOT NULL
LIMIT 5;

-- Check bet_legs were created
SELECT COUNT(*) as total_legs FROM bet_legs;

-- Check players were created  
SELECT COUNT(*) as total_players FROM players;
```

### Check Tax Data
```sql
SELECT user_id, tax_year, total_bets, net_profit
FROM tax_data
ORDER BY tax_year DESC;
```

## What Gets Migrated

### From bet_data JSON:
- `wager` → bets.wager
- `odds` → bets.final_odds  
- `returns` → bets.potential_winnings
- `legs[]` → bet_legs table (individual records)

### Each Leg Creates:
- player record (if new)
- bet_legs record with:
  - Player info
  - Game info
  - Bet details
  - Target/achieved values
  - Status

## New Features After Migration

### 1. Query Individual Legs
```sql
SELECT player_name, bet_type, target_value, achieved_value, is_hit
FROM bet_legs
WHERE player_name = 'Patrick Mahomes';
```

### 2. Player Performance Analysis
```sql
SELECT player_name, 
       COUNT(*) as total_bets,
       SUM(CASE WHEN is_hit THEN 1 ELSE 0 END) as wins,
       ROUND(AVG(CASE WHEN is_hit THEN 100 ELSE 0 END), 1) as win_rate
FROM bet_legs
GROUP BY player_name
HAVING COUNT(*) >= 3
ORDER BY win_rate DESC;
```

### 3. Tax Reports
```sql
SELECT tax_year, total_wagered, total_winnings, net_profit
FROM tax_data
WHERE user_id = 1
ORDER BY tax_year DESC;
```

### 4. Bet Type Analysis
```sql
SELECT bet_type, COUNT(*) as count,
       SUM(CASE WHEN is_hit THEN 1 ELSE 0 END) as wins
FROM bet_legs
GROUP BY bet_type
ORDER BY count DESC;
```

## Troubleshooting

### "DATABASE_URL not set"
```bash
export DATABASE_URL='your_postgresql_connection_string'
```

### "psycopg2 not found"
```bash
pip3 install psycopg2-binary
```

### "Migration already applied"
- Check `schema_migrations` table
- Script automatically skips completed migrations

### "Backup failed"
- Check pg_dump is installed
- Verify DATABASE_URL is correct
- You can skip backup (not recommended for production)

### Data looks wrong after migration
1. Check `bet_legs` count matches expected
2. Verify `players` were created
3. Check `bets` columns populated
4. Restore from backup if needed

## Migration Time Estimates

- **Local (few bets)**: 1-2 minutes
- **Production (100+ bets)**: 5-10 minutes
- **Large database (1000+ bets)**: 15-30 minutes

## Safety Features

1. ✅ **Non-destructive** - Only adds, never deletes
2. ✅ **Transaction-based** - All or nothing
3. ✅ **Backup option** - Create restore point
4. ✅ **Idempotent** - Can run multiple times safely
5. ✅ **Migration tracking** - Knows what's been done
6. ✅ **Rollback ready** - Keep backups for safety

## After Migration

### Next Steps:
1. ✅ Verify data in database
2. ✅ Keep bet_data JSON temporarily (safety)
3. ✅ Update models.py with new structure
4. ✅ Update API endpoints
5. ✅ Update frontend
6. ✅ Test thoroughly
7. ✅ Deploy

### Future Cleanup (optional):
Once you're confident everything works:
- Can remove bet_data JSON column
- Remove JSON parsing code
- Optimize queries for new structure

## Questions?

If you encounter any issues:
1. Check the error message
2. Verify DATABASE_URL is correct
3. Ensure psycopg2 is installed
4. Restore from backup if needed
5. Contact for help with error details
