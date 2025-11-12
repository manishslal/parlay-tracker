# Daily Auto-Deployment for Team Data Updates

## Overview

A GitHub Actions workflow that automatically triggers a Render deployment at 2:00 AM daily, ensuring team data (standings, records, playoff seeds) gets refreshed every morning.

## How It Works

### The Flow

```
2:00 AM Daily
    ↓
GitHub Actions runs
    ↓
Updates LAST_AUTO_UPDATE.txt with timestamp
    ↓
Commits and pushes to main branch
    ↓
Render detects push to main
    ↓
Render auto-deploys app
    ↓
App startup triggers update_team_data_on_startup()
    ↓
Team data refreshed from ESPN API ✅
```

### Why This Approach?

**Problem**: Render doesn't support cron jobs (PaaS limitation)

**Solution**: Use GitHub Actions to trigger deployments
- GitHub Actions has cron support
- Commits to main branch trigger Render auto-deploy
- App startup automation updates team data
- No changes to app code needed!

## Files

### 1. `.github/workflows/daily-deploy.yml`
GitHub Actions workflow that:
- Runs at 2:00 AM Pacific Time (10:00 UTC)
- Updates `LAST_AUTO_UPDATE.txt` with current timestamp
- Commits and pushes to trigger Render deployment
- Can be manually triggered via GitHub UI

### 2. `LAST_AUTO_UPDATE.txt`
Simple timestamp file that gets updated daily:
```
Last auto-update: 2025-11-11 10:00 UTC
```

Purpose: Provides a file to modify that triggers deployment without touching actual code

## Timezone Configuration

The workflow runs at **10:00 UTC** which equals:
- **2:00 AM PST** (Pacific Standard Time, UTC-8)
- **3:00 AM PDT** (Pacific Daylight Time, UTC-7)

To change the schedule, edit the cron expression in `daily-deploy.yml`:

```yaml
schedule:
  - cron: '0 10 * * *'  # 10:00 UTC = 2:00 AM PST
```

### Common Timezones

| Local Time | UTC Cron | Schedule |
|------------|----------|----------|
| 12:00 AM PST | `0 8 * * *` | Midnight |
| 1:00 AM PST | `0 9 * * *` | 1 AM |
| 2:00 AM PST | `0 10 * * *` | 2 AM (current) |
| 3:00 AM PST | `0 11 * * *` | 3 AM |
| 6:00 AM PST | `0 14 * * *` | 6 AM |

## Manual Triggering

You can manually trigger the workflow:

1. Go to GitHub → Actions tab
2. Select "Daily Deployment for Team Data Update"
3. Click "Run workflow"
4. Select branch (main)
5. Click "Run workflow" button

This immediately triggers a deployment without waiting for 2 AM.

## Monitoring

### Check if it's working

**GitHub Actions**:
1. Visit: `https://github.com/manishslal/parlay-tracker/actions`
2. Look for "Daily Deployment for Team Data Update" runs
3. Green checkmark = success ✅
4. Red X = failed ❌

**Render Dashboard**:
1. Visit your Render dashboard
2. Look for deployments at ~2:00 AM daily
3. Check deploy logs for "Team data update completed successfully"

**App Logs**:
Look for these log messages after 2 AM deployments:
```
Starting background team data update...
Team data update completed successfully
```

### What Gets Updated

Every 2 AM deployment refreshes:
- **Team Records**: Wins, losses, ties for all 62 teams
- **Division Rankings**: Current position in division (1st, 2nd, etc.)
- **Playoff Seeds**: AFC/NFC or Conference seeding
- **Streaks**: Win/loss streaks (W3, L2, etc.)
- **Next Games**: Upcoming game dates
- **Games Behind**: Distance from division leader

## Cost

**GitHub Actions**: FREE
- 2,000 minutes/month on free tier
- This workflow uses ~1 minute/day = 30 minutes/month
- Well within free limits ✅

**Render**: NO EXTRA COST
- Just a regular deployment (same as manual push)
- No additional charges

## Troubleshooting

### Workflow Not Running

**Check**:
1. GitHub Actions enabled for repo? (Settings → Actions → General)
2. Workflow file in correct location? (`.github/workflows/daily-deploy.yml`)
3. Cron syntax correct? (Use [crontab.guru](https://crontab.guru))

### Deployment Triggered But Data Not Updated

**Check**:
1. Render logs for "Team data update completed successfully"
2. ESPN API accessible? (Network/firewall issues)
3. `update_team_records.py` script exists and working?
4. Database connection successful?

### Wrong Timezone

**Fix**:
1. Edit `.github/workflows/daily-deploy.yml`
2. Update cron expression (see timezone table above)
3. Commit and push changes

## Disable Auto-Deployments

To stop daily deployments:

**Option 1**: Disable the workflow
1. Go to GitHub → Actions → Select workflow
2. Click "..." menu → "Disable workflow"

**Option 2**: Delete the workflow file
```bash
git rm .github/workflows/daily-deploy.yml
git commit -m "Remove daily auto-deployment"
git push
```

## Alternative: Render Cron Jobs

Render offers cron jobs for **paid plans** ($25+/month):

```yaml
# render.yaml (not currently used)
services:
  - type: web
    name: parlay-tracker
    # ... web service config
    
  - type: cron
    name: team-data-update
    schedule: "0 2 * * *"  # 2:00 AM daily
    command: "python update_team_records.py"
```

**Pros**: 
- Native cron support
- No git commits needed
- Direct execution

**Cons**:
- Requires paid plan
- Additional cost ($7-25/month for cron job)

Current GitHub Actions approach is **free** and works just as well! 🎉

## Summary

✅ **Free solution** using GitHub Actions  
✅ **Automatic** daily deployments at 2 AM  
✅ **Reliable** team data updates via startup automation  
✅ **Monitorable** via GitHub Actions and Render logs  
✅ **Manually triggerable** when needed  
✅ **No code changes** required to app logic  

The deployment triggers Render's existing startup automation (`update_team_data_on_startup()`), which updates all team data from ESPN API. Clean, simple, and free! 🚀
