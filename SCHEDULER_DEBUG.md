# Scheduler Debugging - Why APScheduler Isn't Running

## Investigation Findings

### ✅ Scheduler IS Configured Correctly
- Line 7: `from apscheduler.schedulers.background import BackgroundScheduler`
- ~Line 1990: `scheduler = BackgroundScheduler()`
- Line 2084-2154: 11 jobs added
- Line 2174: `scheduler.start()` called

### ❌ Common Causes for Scheduler Failure on Render

#### 1. **Multiple Worker Processes (MOST LIKELY)**
**Problem**: Gunicorn runs multiple workers, each starting its own scheduler

**What happens:**
- Worker 1 starts → scheduler runs jobs ✅
- Worker 2 starts → scheduler runs same jobs ✅  
- Worker 3 starts → scheduler runs same jobs ✅
- **Result**: Jobs run 3x simultaneously, causing DB locks/conflicts

**Render's Gunicorn Config**:
Render automatically uses multiple workers based on CPU cores.

**Solution**: Use a distributed scheduler OR run jobs in a separate service

#### 2. **Worker Restarts**
**Problem**: Gunicorn restarts workers periodically

**What happens:**
- Worker starts at 2:00 AM
- Jobs scheduled
- Worker killed at 2:29 AM (29 minutes later)
- New worker starts → jobs rescheduled from scratch
- **Result**: Jobs with long intervals might never run

**Render restarts workers**:
- On memory limits
- On deployment
- Every 24 hours (health check)

#### 3. **Execution Environment**
**Problem**: APScheduler doesn't persist state

**What happens:**
- Scheduler stores jobs in memory
- Worker restart = all job history lost
- No way to know if job ran recently

#### 4. **Database Connection Pool Exhaustion**
**Problem**: Background jobs + API requests exceed connection limit

**What happens:**
- Jobs try to run
- Can't get DB connection
- Fail silently or throw error
- Next run attempt has same issue

## How to Verify the Issue

### Check Render Logs for These Patterns:

#### Pattern 1: Multiple workers running jobs
```
[Worker 1] Adding job 'live_bet_updates' to scheduler
[Worker 2] Adding job 'live_bet_updates' to scheduler
[Worker 3] Adding job 'live_bet_updates' to scheduler
```
**Diagnosis**: Multiple workers problem

#### Pattern 2: Worker restarts
```
[INFO] Worker exiting (pid: 12345)
[INFO] Booting worker with pid: 12346
Adding job 'live_bet_updates' to scheduler
```
**Diagnosis**: Worker restart wiping scheduler

#### Pattern 3: Job errors
```
[LIVE-UPDATE] Starting live bet leg update check...
[ERROR] psycopg2.OperationalError: connection pool exhausted
```
**Diagnosis**: Database connection issue

#### Pattern 4: No scheduler logs at all
```
[No logs containing "Adding job" or "[LIVE-UPDATE]"]
```
**Diagnosis**: Scheduler not starting

## Solutions

### Option 1: Separate Background Worker Service (RECOMMENDED)
**Pros**: 
- Single scheduler instance
- No conflicts with API workers
- Can scale independently

**Cons**: 
- Requires separate Render service (extra cost)

**Implementation**:
1. Create new Render Background Worker
2. Run only the scheduler (no Flask app)
3. Point to same database

### Option 2: Use Job Locking
**Pros**:
- Works with multiple workers
- No extra service needed

**Cons**:
- Slightly more complex
- Requires database for locks

**Implementation**:
```python
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

jobstores = {
    'default': SQLAlchemyJobStore(url=DATABASE_URL)
}

executors = {
    'default': ThreadPoolExecutor(10)
}

scheduler = BackgroundScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults={
        'coalesce': True,  # Combine missed runs
        'max_instances': 1  # Only one instance per job
    }
)
```

### Option 3: External Cron Service
**Pros**:
- Simple, reliable
- Many free options (EasyCron, cron-job.org)

**Cons**:
- Requires exposing endpoints
- Need API authentication

**Implementation**:
1. Create `/cron/update-live-bets` endpoint
2. Add API key authentication
3. Set up external cron to hit endpoint every minute

## Recommendation for Render

**BEST FIX**: Option 2 (Job Locking) + Reduce Gunicorn Workers

**Why**:
- Minimal code changes
- No extra cost
- Works with Render's architecture

**Steps**:
1. Add SQLAlchemyJobStore to persist jobs
2. Set `max_instances=1` to prevent duplicates
3. Reduce Gunicorn workers to 2 (reduce conflicts)

Would you like me to implement this fix?
