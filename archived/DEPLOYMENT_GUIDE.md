# 🚀 Multi-User System - Testing & Deployment Guide

## ✅ Implementation Complete!

All code changes have been implemented:

### Backend Changes (app.py):
- ✅ Database configuration (SQLite + SQLAlchemy)
- ✅ Flask-Login setup with session authentication
- ✅ User authentication endpoints (login, register, logout, check)
- ✅ Database helper functions (get_user_bets_from_db, save_bet_to_db, backup_to_json)
- ✅ Updated all routes to use database instead of JSON
- ✅ Added CRUD endpoints for bets (create, update, delete)
- ✅ Database initialization on startup
- ✅ User-specific data filtering (current_user.id)

### Frontend Changes:
- ✅ login.html created (dark theme, mobile-friendly)
- ✅ register.html created (admin-only, password strength indicator)
- ✅ index.html updated:
  - Authentication check on page load
  - Logout via API call
  - Session-based auth (no more token headers)
  - Redirect to login if unauthenticated

### Database Models (models.py):
- ✅ User model with bcrypt password hashing
- ✅ Bet model with user relationship
- ✅ Database indexes for performance

### Migration Script (migrate_to_db.py):
- ✅ One-command migration from JSON to database
- ✅ Interactive admin user creation
- ✅ JSON backup before migration

---

## 🧪 Local Testing Steps

### 1. Install Dependencies
```bash
cd /Users/manishslal/Desktop/Scrapper
pip install -r requirements.txt
```

### 2. Run Migration
```bash
python migrate_to_db.py
```

You'll be prompted to create an admin account:
- Username: (your choice)
- Email: (your choice)
- Password: (strong password)

**Save these credentials! You'll need them to log in.**

### 3. Start the Server
```bash
python app.py
```

Server will start on http://localhost:5001

### 4. Test Authentication

**A. Test Login:**
1. Visit http://localhost:5001/login.html
2. Enter the admin credentials from step 2
3. Should redirect to main app

**B. Test Main App:**
1. Should see your existing bets (from JSON migration)
2. Check hamburger menu - should show "Logout (your_username)"
3. Try switching between tabs (Live, Today's, Historical)

**C. Test Logout:**
1. Click "Logout" in hamburger menu
2. Should redirect to login page
3. Try accessing http://localhost:5001 directly
4. Should auto-redirect to login

**D. Test Registration (Admin Only):**
1. Log in as admin
2. Visit http://localhost:5001/register.html
3. Create a test account:
   - Username: testuser
   - Email: test@example.com
   - Password: testpass123
4. Log out
5. Log in with test account
6. Should see empty bets (data isolation working!)

### 5. Verify JSON Backup
After migration, check these files exist:
- `Data/Todays_Bets.json.backup.<timestamp>`
- `Data/Live_Bets.json.backup.<timestamp>`
- `Data/Historical_Bets.json.backup.<timestamp>`

After creating/updating bets, new JSON files should be created:
- `Data/Todays_Bets.json` (contains user's pending bets)
- `Data/Live_Bets.json` (contains user's live bets)
- `Data/Historical_Bets.json` (contains user's completed bets)

---

## 🚀 Render Deployment

### 1. Commit Changes
```bash
git add .
git commit -m "Implement multi-user authentication system with database migration

- Add Flask-Login, SQLAlchemy, bcrypt dependencies
- Create User and Bet database models
- Add authentication endpoints (login, register, logout)
- Convert all routes from JSON to database queries
- Create login and registration pages
- Update frontend to use session authentication
- Add migration script for JSON to database conversion
- Maintain JSON backup for safety"

git push origin main
```

Render will auto-deploy when you push.

### 2. Run Migration on Render

**A. Access Render Shell:**
1. Go to https://dashboard.render.com
2. Click on "parlay-tracker-backend"
3. Click "Shell" tab
4. Wait for shell to connect

**B. Run Migration:**
```bash
python migrate_to_db.py
```

**C. Create Admin Account:**
- Enter username (e.g., "admin" or your name)
- Enter email (e.g., "admin@example.com")
- Enter strong password
- **SAVE THESE CREDENTIALS!**

**D. Verify Migration:**
Check the output:
- Should show number of bets migrated
- Should show admin user created
- Should show login credentials

### 3. Test Production

**A. Visit Your App:**
https://parlay-tracker-backend.onrender.com/login.html

**B. Login:**
- Use admin credentials from migration
- Should redirect to main app
- Should see your migrated bets

**C. Test PWA Installation:**
1. On iOS: Safari → Share → Add to Home Screen
2. On Android: Chrome → Menu → Install app
3. Open from home screen
4. Should prompt for login
5. After login, should work as PWA

---

## 👥 Creating Beta Tester Accounts

### Option 1: Via Register Page
1. Log in as admin
2. Visit https://parlay-tracker-backend.onrender.com/register.html
3. Create account for each beta tester
4. Share credentials with them

### Option 2: Via Render Shell
```bash
# In Render shell
python
```

```python
from app import app, db
from models import User

with app.app_context():
    # Create user
    user = User(username='friend1', email='friend1@example.com')
    user.set_password('temppassword123')
    db.session.add(user)
    db.session.commit()
    print(f"Created user: {user.username}")
```

Share credentials with beta tester and tell them to change password later.

---

## 🔐 Security Notes

### Production Checklist:
- [ ] Set SECRET_KEY environment variable in Render
  - Go to Render dashboard → Environment → Add variable
  - Name: `SECRET_KEY`
  - Value: Generate with `python -c "import secrets; print(secrets.token_hex(32))"`
  
- [ ] Use HTTPS only (Render provides this automatically)

- [ ] Consider adding password reset functionality (future feature)

- [ ] Consider adding email verification (future feature)

- [ ] Limit registration to admin users (already implemented)

### Environment Variables in Render:
```
SECRET_KEY=<generate with secrets.token_hex(32)>
DATABASE_URL=sqlite:///parlays.db (default, can change to PostgreSQL later)
```

---

## 📊 Database Schema

### Users Table:
```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

### Bets Table:
```sql
CREATE TABLE bet (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    bet_id VARCHAR(100),
    bet_type VARCHAR(50),
    betting_site VARCHAR(50),
    status VARCHAR(20),
    bet_data TEXT,  -- JSON string
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user (id)
);

CREATE INDEX idx_user_status ON bet (user_id, status);
CREATE INDEX idx_user_date ON bet (user_id, created_at);
```

---

## 🐛 Troubleshooting

### Issue: Can't login after migration
**Solution:** Check that migration completed successfully. Check logs for errors.

### Issue: Empty database after migration
**Solution:** Make sure JSON files existed before running migration. Check backup files.

### Issue: "Import error" on startup
**Solution:** Make sure all dependencies are installed: `pip install -r requirements.txt`

### Issue: Database locked error
**Solution:** SQLite doesn't handle concurrent writes well. Consider upgrading to PostgreSQL for production.

### Issue: Can't access register page
**Solution:** Must be logged in as an existing user to access register page.

### Issue: Session expires quickly
**Solution:** This is expected. Add `PERMANENT_SESSION_LIFETIME` to app config if needed.

---

## 📈 Next Steps (Future Enhancements)

1. **Upgrade to PostgreSQL:**
   - Better for concurrent users
   - Add to Render as a service
   - Update DATABASE_URL in app config

2. **Add User Profile Page:**
   - Change password
   - View account stats
   - Delete account

3. **Add Bet Sharing:**
   - Share specific bets with friends
   - View shared bets from others
   - Group leaderboards

4. **Add Password Reset:**
   - Email-based password reset
   - Requires email configuration

5. **Add User Stats Dashboard:**
   - Win/loss ratio
   - Total profit/loss
   - Favorite bet types

6. **Add Social Features:**
   - Follow friends
   - Activity feed
   - Comment on bets

---

## ✅ Verification Checklist

Before considering deployment complete, verify:

- [ ] Migration completed successfully
- [ ] Admin user can log in
- [ ] Bets appear after login
- [ ] Logout works
- [ ] Creating new user works
- [ ] New user sees empty state (data isolation)
- [ ] PWA still works after authentication
- [ ] JSON backups are created
- [ ] All three tabs work (Live, Today's, Historical)
- [ ] Hamburger menu shows username
- [ ] Mobile view looks good
- [ ] 401 errors redirect to login

---

## 📞 Support

If you encounter issues:
1. Check app logs in Render dashboard
2. Check browser console for errors
3. Verify database file exists: `parlays.db`
4. Check that SECRET_KEY is set in Render environment

---

**🎉 Congratulations! Your parlay tracker now supports multiple users with secure authentication!**
