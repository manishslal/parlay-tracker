# Render Deployment Fix - Missing Database Tables

## The Problem

Your Render deployment is showing this error:
```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
```

This means the database tables haven't been created in production.

## The Solution

### 1. Configure Render Build Command

In your Render dashboard:

1. Go to your service: **parlay-tracker-backend**
2. Go to **Settings** → **Build & Deploy**
3. Update **Build Command** to:
   ```bash
   ./build.sh
   ```

This will:
- Install dependencies
- Create all database tables
- Run all migrations automatically on each deploy

### 2. Alternative: Manual Database Initialization

If you prefer to initialize manually, you can run this command in Render Shell:

```bash
python init_db.py
```

To access Render Shell:
1. Go to your service dashboard
2. Click **Shell** tab
3. Run the command above

### 3. Files Added

**`init_db.py`** - Database initialization script
- Creates all tables (users, bets)
- Verifies all columns exist
- Shows helpful next steps

**`build.sh`** - Automated build script
- Runs `pip install -r requirements.txt`
- Runs `python init_db.py`
- Ensures database is ready before deployment

## What Gets Created

### Tables

**`users` table:**
- id, username, email, password_hash
- created_at, is_active

**`bets` table:**
- id, user_id, bet_id, bet_type, betting_site
- status, is_active, is_archived, api_fetched
- bet_data (JSON), created_at, updated_at, bet_date

### Indexes
- idx_user_status (user_id, status)
- idx_user_date (user_id, bet_date)

## After Database Initialization

### Step 1: Register a User

**Endpoint:** `POST /auth/register`

**Body:**
```json
{
  "username": "manishslal",
  "email": "your-email@example.com",
  "password": "your-secure-password"
}
```

**Using curl:**
```bash
curl -X POST https://parlay-tracker-backend.onrender.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "manishslal",
    "email": "your-email@example.com",
    "password": "your-password"
  }'
```

### Step 2: Login

**Endpoint:** `POST /auth/login`

**Body:**
```json
{
  "username": "manishslal",
  "password": "your-password"
}
```

This will create a session and allow you to use the app.

### Step 3: Start Using the App

Now you can:
- Login from your iPhone at `https://parlay-tracker-backend.onrender.com/login.html`
- Add bets
- Track parlays

## Render Dashboard Configuration

### Environment Variables

Make sure these are set in Render:
- `SECRET_KEY` - Flask secret key (random string)
- `FLASK_ENV` - Set to `production`

### Build Settings

**Build Command:** `./build.sh`
**Start Command:** `gunicorn app:app`

### Important Notes

1. **SQLite on Render**: SQLite database files are ephemeral on Render's free tier. The database will reset if the service restarts. For production, consider:
   - Upgrading to persistent storage
   - Using PostgreSQL instead of SQLite

2. **Database Persistence**: To keep your data:
   - Enable "Persistent Disk" in Render settings
   - Or migrate to PostgreSQL for production use

3. **First Time Setup**: After deploying with the build script, you need to register at least one user before logging in.

## Quick Fix Steps

### Option A: Redeploy with Build Script (Recommended)

1. **Update Render Settings:**
   - Build Command: `./build.sh`
   - This will auto-initialize database on every deploy

2. **Trigger Redeploy:**
   - Push this commit to GitHub
   - Render will auto-deploy
   - Database will be initialized automatically

3. **Register Your User:**
   - Go to `/auth/register` endpoint
   - Create your user account

### Option B: Manual Shell Initialization

1. **Go to Render Dashboard** → Your Service → Shell
2. **Run:** `python init_db.py`
3. **Go to your app** and register a user

## Testing the Fix

### 1. Check Database Initialization

In Render Shell:
```bash
python init_db.py
```

Expected output:
```
✅ Tables created successfully
✅ Found tables: users, bets
✅ All required columns present
✅ DATABASE INITIALIZATION COMPLETE
```

### 2. Verify Tables Exist

```bash
python -c "from app import app, db; from models import User, Bet; app.app_context().push(); print(f'Users: {User.query.count()}'); print(f'Bets: {Bet.query.count()}')"
```

### 3. Test Registration

```bash
curl -X POST https://parlay-tracker-backend.onrender.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@test.com","password":"test123"}'
```

Expected: `{"message": "User created successfully", ...}`

### 4. Test Login

```bash
curl -X POST https://parlay-tracker-backend.onrender.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"test123"}'
```

Expected: `{"message": "Login successful", ...}`

## Migration to PostgreSQL (Optional)

For production use, consider PostgreSQL:

### 1. Add PostgreSQL to Render
1. Dashboard → New → PostgreSQL
2. Create database
3. Get connection string

### 2. Update app.py
```python
# Replace
SQLALCHEMY_DATABASE_URI = 'sqlite:///parlays.db'

# With
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///parlays.db')
```

### 3. Set Environment Variable
In Render:
- Add `DATABASE_URL` = `[your-postgres-connection-string]`

### 4. Update requirements.txt
```
psycopg2-binary==2.9.9
```

## Troubleshooting

### Error: "no such table: users"
**Solution:** Run `python init_db.py` in Render Shell or redeploy with build script

### Error: "no such column: api_fetched"
**Solution:** Database was created before migration. Run `python migrate_add_api_fetched.py`

### Error: "User already exists"
**Solution:** User was already registered. Try logging in instead.

### Database resets after restart
**Solution:** 
- Option 1: Enable Persistent Disk in Render (paid)
- Option 2: Migrate to PostgreSQL database

## Summary

1. ✅ Add `init_db.py` and `build.sh` to repo
2. ✅ Update Render Build Command to `./build.sh`
3. ✅ Push to GitHub (auto-deploy)
4. ✅ Register a user via `/auth/register`
5. ✅ Login and use the app!

Your production database will now be properly initialized on every deployment! 🚀
