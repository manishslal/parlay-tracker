# 🎯 Multi-User System Implementation Plan

## Phase 3C: Full Multi-User System - Implementation Guide

### Current Progress:
✅ Updated requirements.txt with Flask-Login, SQLAlchemy, bcrypt
✅ Created models.py with User and Bet models
✅ Created migrate_to_db.py migration script

### Next Steps:

#### 1. Update app.py (MAJOR CHANGES)
**What needs to change:**
- Add database initialization
- Add Flask-Login setup
- Replace all JSON file operations with database queries
- Add user authentication to all API endpoints
- Add registration and login endpoints
- Filter all bet queries by current_user.id

**Files to modify:**
- `app.py` - Complete rewrite of data layer

#### 2. Create Authentication UI
**New files to create:**
- `login.html` - Login page
- `register.html` - Registration page

**Files to modify:**
- `index.html` - Add username display in menu, redirect if not logged in

#### 3. Update Frontend JavaScript
**What needs to change:**
- Replace token-based auth with session-based auth
- Handle login/logout redirects
- Show current user in menu
- Update API calls (no more manual token passing)

#### 4. Testing & Migration
**Steps:**
- Run migration script locally
- Test user registration
- Test login/logout
- Test bet creation as different users
- Verify data isolation
- Deploy to Render

---

## 📝 Detailed Implementation Plan

### Part 1: Backend (app.py)

**A. Database Setup:**
```python
from models import db, User, Bet
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parlays.db'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
```

**B. Replace Data Functions:**
- `load_parlays()` → `Bet.query.filter_by(user_id=current_user.id, status='pending').all()`
- `load_live_parlays()` → `Bet.query.filter_by(user_id=current_user.id, status='live').all()`
- `load_historical_bets()` → `Bet.query.filter_by(user_id=current_user.id, status__in=['won', 'lost']).all()`
- Remove all JSON file read/write operations

**C. Add New Endpoints:**
```python
@app.route('/auth/register', methods=['POST'])
@app.route('/auth/login', methods=['POST'])
@app.route('/auth/logout', methods=['POST'])
@app.route('/auth/check', methods=['GET'])
```

**D. Update Existing Endpoints:**
- Add `@login_required` decorator to all bet endpoints
- Filter queries by `current_user.id`
- Update responses to use `bet.to_dict()`

### Part 2: Frontend (HTML/JS)

**A. Create Login Page:**
- Simple form with username/password
- Error message display
- Link to registration
- Redirect to main app after login

**B. Create Registration Page:**
- Form with username, email, password, confirm password
- Validation
- Link to login
- Auto-login after registration

**C. Update Main App:**
- Check if logged in on page load
- Redirect to /login if not authenticated
- Show username in hamburger menu
- Update logout to call /auth/logout endpoint

### Part 3: Migration & Deployment

**A. Local Migration:**
1. Run `python migrate_to_db.py`
2. Create admin user
3. Test locally

**B. Render Deployment:**
1. Commit all changes
2. Push to GitHub
3. Render auto-deploys
4. Run migration on Render via Shell
5. Create users for beta testers

---

## 🚀 Let's Proceed!

This is a substantial change. Would you like me to:

**Option 1: Do it all at once** (I'll update all files, commit, and push)
- Pros: Fast, complete
- Cons: Big bang, harder to debug if issues

**Option 2: Step by step** (We do each part separately and test)
- Pros: Safer, can test each piece
- Cons: Takes longer, more commits

**Option 3: Create a new branch first** (Make changes in a feature branch)
- Pros: Can test without affecting production
- Cons: Need to manage branches

Which approach would you prefer?

Also, quick question: Do you want to keep the old JSON-based system as a fallback, or fully commit to the database?
