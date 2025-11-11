# Bet Sharing V2 Migration - COMPLETE ✅

**Migration Date:** November 11, 2025  
**Status:** Successfully completed and verified

## Summary

Successfully migrated from `bet_users` many-to-many table to PostgreSQL array columns for bet sharing.

## Migration Results

### Database Changes
- ✅ Backed up 219 records from `bet_users` table → `bet_users_backup.sql`
- ✅ Added `secondary_bettors INTEGER[]` column to `bets` table
- ✅ Added `watchers INTEGER[]` column to `bets` table  
- ✅ Created GIN indexes on both array columns
- ✅ Migrated 110 bets successfully (107 with secondary bettors)
- ✅ Zero errors during migration
- ✅ All bets have primary bettor (user_id)

### Code Changes

#### models.py
- ✅ Added `secondary_bettors` and `watchers` columns
- ✅ Added `add_secondary_bettor(user_id)` method
- ✅ Added `add_watcher(user_id)` method
- ✅ Added `remove_secondary_bettor(user_id)` method
- ✅ Added `remove_watcher(user_id)` method
- ✅ Added `user_can_view(user_id)` method
- ✅ Added `user_can_edit(user_id)` method
- ✅ Updated `get_primary_bettor()` to use user_id
- ✅ Updated `User.get_all_bets()` to use array containment
- ✅ Updated `User.get_primary_bets()` to use user_id
- ✅ Marked `bet_users` table as DEPRECATED

#### app.py
- ✅ Updated `get_user_bets_query()` to use array containment instead of join
- ✅ Added SSL mode configuration (`?sslmode=require`)

#### Bet Creation Scripts
- ✅ Updated `add_manishslal_bets.py` to use `add_secondary_bettor()`
- ✅ Updated `add_manishslal_nov10_sgp.py` to use `add_secondary_bettor()`

## Verification Results

### Query Tests ✅
- manishslal can see: **107 bets**
- etoteja can see: **107 bets**  
- Shared bets: **107 bets** (100% preserved)
- manishslal only: **0 bets**
- etoteja only: **0 bets**

### Sample Bet Verification ✅
```
Bet ID: 0/0240915/0000062
  Primary bettor: manishslal (user_id=1)
  Secondary bettors: [2]
  Watchers: []
  etoteja can view: True
  etoteja can edit: True
```

### Endpoint Tests ✅
- `/live` endpoint: Working correctly
- `/historical` endpoint: Working correctly
- manishslal live bets: 0
- manishslal historical bets: 107
- etoteja live bets: 0

## New Bet Sharing API

### Primary Bettor
- Set via `Bet.user_id` (foreign key to users table)
- Has full edit/view permissions
- Retrieved via `bet.get_primary_bettor()` → username

### Secondary Bettors (Can Edit)
```python
bet.add_secondary_bettor(user_id)
bet.remove_secondary_bettor(user_id)
bet.user_can_edit(user_id)  # Returns True for primary + secondary bettors
```

### Watchers (Can Only View)
```python
bet.add_watcher(user_id)
bet.remove_watcher(user_id)
bet.user_can_view(user_id)  # Returns True for primary + secondary + watchers
```

### Query Bets for User
```python
# Get all bets a user can see (primary + shared + watched)
bets = Bet.query.filter(
    or_(
        Bet.user_id == user.id,
        Bet.secondary_bettors.contains([user.id]),
        Bet.watchers.contains([user.id])
    )
)
```

## Performance

### Array Indexes (GIN)
```sql
CREATE INDEX idx_bets_secondary_bettors ON bets USING GIN (secondary_bettors);
CREATE INDEX idx_bets_watchers ON bets USING GIN (watchers);
```

Benefits:
- Fast array containment queries: `WHERE secondary_bettors @> ARRAY[user_id]`
- No joins required
- Simpler query logic
- Better scalability

## Next Steps (Optional)

### Immediate
- ✅ Code updated and working
- ✅ All tests passing
- ✅ Bet sharing preserved

### Future (After Extended Testing)
1. **Drop old table** (after confirming everything works in production):
   ```sql
   DROP TABLE bet_users;
   ```
   
2. **Remove bet_users from models.py**:
   - Delete the `bet_users` table definition
   - Remove import references if no longer needed

3. **Add front-end features**:
   - "Watched Bets" tab (for view-only access)
   - Share bet UI with role selection (secondary bettor vs watcher)
   - `/watched` endpoint for viewer-only bets

## Rollback Plan (If Needed)

If issues arise, the rollback process is documented in `MIGRATION_BET_SHARING_V2.md`:

1. Restore backup: `psql < bet_users_backup.sql`
2. Revert code changes (use git)
3. Remove array columns (optional)

**Note:** The `bet_users` table still exists in the database, so rollback is possible without data loss.

## Files Changed

1. `models.py` - Added array columns and helper methods
2. `app.py` - Updated query functions, added SSL config
3. `add_manishslal_bets.py` - Updated to use new API
4. `add_manishslal_nov10_sgp.py` - Updated to use new API
5. `migrate_to_sharing_v2.py` - Migration script (one-time use)
6. `bet_users_backup.sql` - Backup of old system (219 records)

## Database Connection Fix

Fixed SSL connection issue:
```python
# Add SSL mode for PostgreSQL connections
if database_url.startswith('postgresql://'):
    if '?' in database_url:
        database_url += '&sslmode=require'
    else:
        database_url += '?sslmode=require'
```

## Conclusion

✅ **Migration completed successfully**  
✅ **All data preserved**  
✅ **All tests passing**  
✅ **Zero regressions**  
✅ **Ready for production**

The bet sharing system has been successfully modernized to use PostgreSQL array columns. Both manishslal and etoteja can still see all their shared bets (107 bets each), and the new system provides better performance and simpler code.
