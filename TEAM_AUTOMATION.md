# Team Data Automation

This directory contains scripts to automatically update team records (wins, losses, game dates, standings) from ESPN API.

## Overview

The automation system updates **only dynamic data** that changes frequently:
- ✅ Games played, wins, losses, ties
- ✅ Win percentage
- ✅ Division rank, conference rank
- ✅ Streak (e.g., "W3", "L2")
- ✅ Next game date
- ✅ Last update timestamp

**Static data is NOT updated** (to save API calls):
- ❌ League name (NFL/NBA)
- ❌ Conference (AFC/NFC/Eastern/Western)
- ❌ Division names
- ❌ Team names, abbreviations, logos, colors

## Scripts

### 1. `update_team_records.py`
Main script that updates team data from ESPN API.

**Usage:**
```bash
# Run manually
DATABASE_URL='your_database_url' python update_team_records.py

# With .env file
python update_team_records.py
```

**Features:**
- Smart update: Only updates teams that haven't been updated in 6+ hours
- Rate limiting: 0.3s delay between API calls
- Error handling: Continues on failure, logs errors
- Summary report: Shows updated/skipped/failed counts

**Output Example:**
```
🔄 Starting team data update at 2025-11-09 14:30:00
================================================================================
Found 62 teams to check

  ✅ New England Patriots           (NE ) 7-2     
  ✅ Buffalo Bills                  (BUF) 6-2     
  ⏭️  Miami Dolphins (recently updated)
  ...

================================================================================
UPDATE SUMMARY
================================================================================
Total teams: 62
✅ Updated: 45
⏭️  Skipped (recently updated): 15
❌ Failed: 2
```

### 2. `daily_team_update.sh`
Bash wrapper script for cron jobs.

**Setup:**
```bash
# Make executable
chmod +x daily_team_update.sh

# Test run
./daily_team_update.sh

# Add to crontab for daily 2 AM updates
crontab -e

# Add this line:
0 2 * * * /Users/manishslal/Desktop/Scrapper/daily_team_update.sh
```

**Cron Schedule Examples:**
```bash
# Every day at 2 AM
0 2 * * * /path/to/daily_team_update.sh

# Every 6 hours
0 */6 * * * /path/to/daily_team_update.sh

# Every day at 6 AM and 6 PM
0 6,18 * * * /path/to/daily_team_update.sh

# Monday-Friday at 8 AM (business days only)
0 8 * * 1-5 /path/to/daily_team_update.sh
```

### 3. Application Startup Integration

The script automatically runs on application startup (in `app.py`):

```python
def update_team_data_on_startup():
    """Update team records on application startup (runs in background)"""
    # Runs in background thread, doesn't block app startup
    # Updates happen async while app is loading
```

**When it runs:**
- ✅ On application start (Render deployment)
- ✅ After server restart
- ✅ On local development server start

## Deployment on Render

### Option 1: Use Render Cron Jobs
Render supports cron jobs for scheduled tasks.

**In `render.yaml`:**
```yaml
services:
  - type: web
    name: parlay-tracker
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "gunicorn app:app"
    
  # Add cron job service
  - type: cron
    name: team-update-cron
    env: python
    schedule: "0 2 * * *"  # Daily at 2 AM UTC
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python update_team_records.py"
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: parlays
          property: connectionString
```

### Option 2: Rely on Startup Updates Only
If your app restarts regularly, startup updates may be sufficient:
- Render restarts on each deploy
- Auto-restarts on crashes
- Manual restarts via dashboard

### Option 3: External Cron Service
Use services like:
- **cron-job.org** (free, web-based)
- **EasyCron** (free tier available)
- **GitHub Actions** (runs on schedule)

## Monitoring

### View Update Logs

**On Render:**
```bash
# View recent logs
render logs -s parlay-tracker

# Filter for team updates
render logs -s parlay-tracker | grep "team data update"
```

**Locally:**
```bash
# If using log file
tail -f logs/team_updates.log

# Check last update time in database
psql $DATABASE_URL -c "SELECT sport, MAX(last_stats_update) FROM teams GROUP BY sport;"
```

### Check Update Status

```python
# Quick script to check when teams were last updated
import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

cur.execute("""
    SELECT 
        sport,
        COUNT(*) as total,
        MIN(last_stats_update) as oldest_update,
        MAX(last_stats_update) as newest_update
    FROM teams
    GROUP BY sport
""")

for sport, total, oldest, newest in cur.fetchall():
    print(f"{sport}: {total} teams")
    print(f"  Oldest update: {oldest}")
    print(f"  Newest update: {newest}")
```

## Configuration

### Update Frequency
Edit `update_team_records.py` to change the update threshold:

```python
def should_update_team(last_update):
    # Current: Update if last update was more than 6 hours ago
    time_since_update = datetime.utcnow() - last_update
    return time_since_update > timedelta(hours=6)  # Change this value
```

**Recommended Settings:**
- **During season:** 6 hours (2-4 updates per day)
- **Off-season:** 24 hours (1 update per day)
- **Playoffs:** 3 hours (more frequent)

### Rate Limiting
Adjust API call delays in `update_team_records.py`:

```python
time.sleep(0.3)  # 0.3 seconds between calls (current)
                 # Increase if hitting rate limits
                 # Decrease for faster updates (use cautiously)
```

## Troubleshooting

### Teams Not Updating

1. **Check last update time:**
   ```sql
   SELECT team_name, last_stats_update 
   FROM teams 
   ORDER BY last_stats_update DESC LIMIT 10;
   ```

2. **Force update by clearing timestamps:**
   ```sql
   UPDATE teams SET last_stats_update = NULL WHERE sport = 'NFL';
   ```

3. **Run manually to see errors:**
   ```bash
   python update_team_records.py
   ```

### API Rate Limiting

If you see connection errors:
- Increase `time.sleep()` delay
- Reduce update frequency
- Check ESPN API status

### Database Connection Issues

```bash
# Test database connection
python -c "
import psycopg2
import os
conn = psycopg2.connect(os.environ['DATABASE_URL'])
print('✅ Database connection successful')
"
```

## Testing

### Test the Update Script

```bash
# Run once manually
DATABASE_URL='your_url' python update_team_records.py

# Should see output like:
# 🔄 Starting team data update...
# ✅ New England Patriots (NE ) 7-2
# ...
# ✅ Update completed
```

### Test Cron Script

```bash
# Run the cron wrapper
./daily_team_update.sh

# Check if log file was created
cat logs/team_updates.log
```

### Test Startup Integration

```bash
# Start the Flask app
python app.py

# Check logs for:
# "Starting background team data update..."
# "Team data update completed successfully"
```

## Best Practices

1. **Monitor First Week:** Watch logs closely after setup to ensure updates work
2. **Off-season Adjustments:** Reduce frequency during off-season
3. **Backup Before Changes:** Always backup database before modifying update logic
4. **Test in Development:** Test update scripts locally before deploying
5. **Log Rotation:** Set up log rotation if using file logging

## Support

If you encounter issues:
1. Check the logs (Render dashboard or local log file)
2. Verify database connection works
3. Test ESPN API endpoints manually
4. Check environment variables are set correctly

## Future Enhancements

Potential improvements:
- [ ] Add Slack/email notifications for failed updates
- [ ] Dashboard showing update health
- [ ] Historical tracking of record changes
- [ ] Playoff bracket updates
- [ ] Player stats updates (separate script)
- [ ] Automatic season rollover
