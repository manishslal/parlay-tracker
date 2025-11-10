# Team Data Automation - Quick Reference

## 🚀 Quick Start

The system is already set up and running! Team data automatically updates:
- ✅ On application startup (already integrated in `app.py`)
- ✅ Every 6 hours when you run the update script
- ✅ On demand via admin endpoint or manual script

## 📋 What Gets Updated Automatically

**Updated Fields** (dynamic data):
- Games played, wins, losses, ties
- Win percentage
- Division rank, conference rank
- Winning/losing streak
- Next game date
- Last update timestamp

**NOT Updated** (static data):
- Team names, abbreviations
- League, conference, division names
- Logos, colors
- ESPN team IDs

## 🛠️ Commands

### Check Current Status
```bash
# See when teams were last updated
DATABASE_URL='your_url' python -c "
import psycopg2, os
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()
cur.execute('SELECT sport, MAX(last_stats_update) FROM teams GROUP BY sport')
for sport, last_update in cur.fetchall():
    print(f'{sport}: Last updated {last_update}')
"
```

### Manual Update (Smart)
Updates only teams not updated in 6+ hours:
```bash
DATABASE_URL='your_url' python update_team_records.py
```

### Force Update (All Teams)
Updates ALL teams immediately:
```bash
DATABASE_URL='your_url' python force_team_update.py
```

### Via Web Admin Endpoint
```bash
# Call from JavaScript or curl
curl -X POST https://your-app.com/admin/update_teams \
  -H "Content-Type: application/json" \
  --cookie "session=your_session_cookie"
```

## 📅 Automation Options

### Option 1: Render Deployment (Automatic)
✅ **Already enabled!** Updates run on every app start.

Your app automatically updates team data when:
- Deployed to Render
- Restarted
- After a crash recovery

**No additional setup needed!**

### Option 2: Daily Cron Job (Local/Server)
For daily updates at 2 AM:

```bash
# Open crontab editor
crontab -e

# Add this line (updates daily at 2 AM)
0 2 * * * cd /Users/manishslal/Desktop/Scrapper && ./daily_team_update.sh

# Save and exit
```

**Verify cron job:**
```bash
# List current cron jobs
crontab -l

# Check logs
tail -f logs/team_updates.log
```

### Option 3: Render Cron Jobs
Add to `render.yaml`:

```yaml
services:
  # Your existing web service
  - type: web
    name: parlay-tracker
    # ... existing config ...
    
  # Add this new cron service
  - type: cron
    name: team-update-cron
    env: python
    schedule: "0 */6 * * *"  # Every 6 hours
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python update_team_records.py"
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: parlays
          property: connectionString
```

## 🔍 Monitoring

### View Last Update Times
```sql
-- In psql or database client
SELECT 
    team_name,
    team_abbr,
    sport,
    wins,
    losses,
    last_stats_update
FROM teams
ORDER BY last_stats_update DESC
LIMIT 20;
```

### Check Update Logs (if using cron)
```bash
# View recent updates
tail -20 logs/team_updates.log

# Watch live updates
tail -f logs/team_updates.log

# Search for errors
grep "Failed" logs/team_updates.log
```

### View Render Logs
```bash
# In Render dashboard, go to your service → Logs
# Or use Render CLI:
render logs -s parlay-tracker | grep "team data"
```

## 🐛 Troubleshooting

### Teams Not Updating

**Problem:** Data seems stale

**Solution:**
```bash
# Force immediate update
DATABASE_URL='your_url' python force_team_update.py
```

### Script Not Running on Startup

**Check app logs for:**
- "Starting background team data update..."
- "Team data update completed successfully"

**If missing:**
- Verify `app.py` has the startup function
- Check DATABASE_URL is set
- Look for error messages in logs

### Cron Job Not Working

**Test manually first:**
```bash
cd /Users/manishslal/Desktop/Scrapper
./daily_team_update.sh
```

**Check cron logs:**
```bash
# macOS
tail -f /var/log/system.log | grep cron

# Linux
tail -f /var/log/syslog | grep CRON
```

**Common issues:**
- Script not executable: `chmod +x daily_team_update.sh`
- Wrong path in crontab: Use absolute paths
- Environment variables not set: Add to script or use `.env` file

## 📊 Update Frequency Recommendations

**During Regular Season:**
- Update every 6-12 hours
- More frequent during game days

**During Playoffs:**
- Update every 3-6 hours
- Daily updates minimum

**Off-Season:**
- Update once per day or less
- Can reduce to weekly

## 🎯 Best Practices

1. **Let Startup Handle It:** The app startup update is usually sufficient
2. **Add Cron for Reliability:** If app doesn't restart often, add cron job
3. **Monitor First Week:** Check logs daily after setup
4. **Force Update Sparingly:** Only when data is truly stale
5. **Check Before Games:** Force update before big game days

## 📞 Quick Help

**Data looks wrong?**
```bash
# Force fresh update
DATABASE_URL='your_url' python force_team_update.py
```

**Want to update just one sport?**
```sql
-- Clear timestamps for NFL only
UPDATE teams SET last_stats_update = NULL WHERE sport = 'NFL';

-- Then run update script
python update_team_records.py
```

**Need to update more frequently?**
Edit `update_team_records.py`:
```python
# Change line ~97 from:
return time_since_update > timedelta(hours=6)
# To:
return time_since_update > timedelta(hours=3)  # Update every 3 hours
```

## ✅ Current Status

Your system is **fully automated** and ready to use!

- ✅ Teams table populated (32 NFL + 30 NBA)
- ✅ Update script created and tested
- ✅ App startup integration enabled
- ✅ Cron script ready (optional)
- ✅ Admin endpoint available
- ✅ Force update tool ready

**Next Steps:**
1. Deploy to Render (updates will run automatically)
2. Optionally set up cron job for redundancy
3. Monitor logs for first few days
4. Enjoy automatic team data updates! 🎉
