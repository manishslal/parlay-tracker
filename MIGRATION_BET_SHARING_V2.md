# Migration Plan: Bet Sharing System V2

## Overview
Moving from many-to-many (bet_users table) to one-to-many with array columns for better clarity and flexibility.

## Database Changes

### Step 1: Add New Columns to bets Table

```sql
-- Add array columns to bets table
ALTER TABLE bets 
ADD COLUMN secondary_bettors INTEGER[] DEFAULT '{}',
ADD COLUMN watchers INTEGER[] DEFAULT '{}';

-- Add index for searching in arrays
CREATE INDEX idx_bets_secondary_bettors ON bets USING GIN(secondary_bettors);
CREATE INDEX idx_bets_watchers ON bets USING GIN(watchers);
```

### Step 2: Migrate Existing Data

```sql
-- Migrate existing bet_users data to new structure
UPDATE bets
SET 
    user_id = (
        SELECT user_id 
        FROM bet_users 
        WHERE bet_users.bet_id = bets.id 
        AND bet_users.is_primary_bettor = TRUE
        LIMIT 1
    ),
    secondary_bettors = (
        SELECT ARRAY_AGG(user_id)
        FROM bet_users
        WHERE bet_users.bet_id = bets.id
        AND bet_users.is_primary_bettor = FALSE
    );

-- Set empty arrays for bets with no secondary bettors
UPDATE bets
SET secondary_bettors = '{}'
WHERE secondary_bettors IS NULL;

UPDATE bets
SET watchers = '{}'
WHERE watchers IS NULL;
```

### Step 3: Verify Migration

```sql
-- Check that all bets have a primary bettor
SELECT COUNT(*) FROM bets WHERE user_id IS NULL;
-- Should return 0

-- Check migrated data
SELECT 
    id,
    bet_id,
    user_id,
    secondary_bettors,
    watchers
FROM bets
WHERE array_length(secondary_bettors, 1) > 0
LIMIT 10;
```

### Step 4: Drop Old Table (After Verification)

```sql
-- ONLY after confirming everything works!
DROP TABLE bet_users;
```

## Code Changes

### 1. Update models.py

**Remove:**
- `bet_users` table definition
- `User.shared_bets` relationship
- `Bet.add_user()` method
- `Bet.remove_user()` method
- `User.get_all_bets()` method

**Add:**
```python
class Bet(db.Model):
    # ... existing columns ...
    
    # New columns
    secondary_bettors = db.Column(db.ARRAY(db.Integer), default=[])
    watchers = db.Column(db.ARRAY(db.Integer), default=[])
    
    def add_secondary_bettor(self, user):
        """Add a user as secondary bettor"""
        if user.id not in (self.secondary_bettors or []):
            if self.secondary_bettors is None:
                self.secondary_bettors = []
            self.secondary_bettors = self.secondary_bettors + [user.id]
            db.session.commit()
    
    def remove_secondary_bettor(self, user):
        """Remove a user from secondary bettors"""
        if self.secondary_bettors and user.id in self.secondary_bettors:
            self.secondary_bettors = [uid for uid in self.secondary_bettors if uid != user.id]
            db.session.commit()
    
    def add_watcher(self, user):
        """Add a user as watcher"""
        if user.id not in (self.watchers or []):
            if self.watchers is None:
                self.watchers = []
            self.watchers = self.watchers + [user.id]
            db.session.commit()
    
    def remove_watcher(self, user):
        """Remove a user from watchers"""
        if self.watchers and user.id in self.watchers:
            self.watchers = [uid for uid in self.watchers if uid != user.id]
            db.session.commit()
    
    def get_all_bettors(self):
        """Get primary bettor + secondary bettors"""
        bettors = [self.user_id]
        if self.secondary_bettors:
            bettors.extend(self.secondary_bettors)
        return User.query.filter(User.id.in_(bettors)).all()
    
    def get_all_viewers(self):
        """Get watchers (non-bettors)"""
        if not self.watchers:
            return []
        return User.query.filter(User.id.in_(self.watchers)).all()
    
    def user_can_view(self, user):
        """Check if user can view this bet"""
        if user.id == self.user_id:
            return True
        if self.secondary_bettors and user.id in self.secondary_bettors:
            return True
        if self.watchers and user.id in self.watchers:
            return True
        return False
```

### 2. Update app.py

**Replace `get_user_bets_query()`:**

```python
def get_user_bets_query(user, is_active=None, is_archived=None, status=None):
    """Get bets visible to a user (primary, secondary, or watcher)"""
    from sqlalchemy import or_
    
    query = Bet.query.filter(
        or_(
            Bet.user_id == user.id,  # Primary bettor
            Bet.secondary_bettors.contains([user.id]),  # Secondary bettor
            Bet.watchers.contains([user.id])  # Watcher
        )
    )
    
    if is_active is not None:
        query = query.filter(Bet.is_active == is_active)
    if is_archived is not None:
        query = query.filter(Bet.is_archived == is_archived)
    if status:
        query = query.filter(Bet.status == status)
    
    return query

def get_user_bets_by_role(user, role='all', is_active=None):
    """Get bets filtered by user's role
    
    Args:
        role: 'primary', 'secondary', 'watcher', or 'all'
    """
    if role == 'primary':
        query = Bet.query.filter(Bet.user_id == user.id)
    elif role == 'secondary':
        query = Bet.query.filter(Bet.secondary_bettors.contains([user.id]))
    elif role == 'watcher':
        query = Bet.query.filter(Bet.watchers.contains([user.id]))
    else:  # 'all'
        return get_user_bets_query(user, is_active=is_active)
    
    if is_active is not None:
        query = query.filter(Bet.is_active == is_active)
    
    return query
```

**Add new endpoints:**

```python
@app.route("/watched")
@login_required
def watched():
    """Show bets user is watching (not betting on)"""
    bets = get_user_bets_by_role(
        current_user,
        role='watcher',
        is_active=True
    ).all()
    
    watched_parlays = [bet.to_dict_structured(use_live_data=True) for bet in bets]
    processed = process_parlay_data(watched_parlays)
    return jsonify(sort_parlays_by_date(processed))

@app.route("/api/bets/<int:bet_id>/share", methods=['POST'])
@login_required
def share_bet(bet_id):
    """Share a bet with other users"""
    bet = Bet.query.get_or_404(bet_id)
    
    # Only primary bettor can share
    if bet.user_id != current_user.id:
        return jsonify({'error': 'Only the primary bettor can share this bet'}), 403
    
    data = request.json
    username = data.get('username')
    role = data.get('role', 'watcher')  # 'secondary' or 'watcher'
    
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if role == 'secondary':
        bet.add_secondary_bettor(user)
    else:
        bet.add_watcher(user)
    
    return jsonify({
        'success': True,
        'message': f'Bet shared with {username} as {role}'
    })
```

### 3. Update to_dict_structured()

```python
def to_dict_structured(self, use_live_data=False):
    """Convert bet to dictionary using structured database tables"""
    # ... existing code ...
    
    # Add bettor info
    bet_dict['primary_bettor'] = self.user.username if self.user else 'Unknown'
    
    # Add secondary bettors
    if self.secondary_bettors:
        secondary_users = User.query.filter(User.id.in_(self.secondary_bettors)).all()
        bet_dict['secondary_bettors'] = [u.username for u in secondary_users]
    else:
        bet_dict['secondary_bettors'] = []
    
    # Add watchers
    if self.watchers:
        watcher_users = User.query.filter(User.id.in_(self.watchers)).all()
        bet_dict['watchers'] = [u.username for u in watcher_users]
    else:
        bet_dict['watchers'] = []
    
    # Determine user's role in this bet (for current_user context)
    bet_dict['user_role'] = 'none'
    # This would be set by the endpoint based on current_user
    
    return bet_dict
```

## Front End Changes

### 1. Update Navigation

**Add "Watched Bets" tab:**
```javascript
// In index.html or app.js
const tabs = [
  { id: 'live', label: 'Live Bets', endpoint: '/live' },
  { id: 'watched', label: 'Watched Bets', endpoint: '/watched' },  // NEW
  { id: 'todays', label: "Today's Bets", endpoint: '/todays' },
  { id: 'historical', label: 'Historical', endpoint: '/historical' }
];
```

### 2. Update Bet Display

```javascript
function renderBet(bet, currentUser) {
  let bettorLabel = '';
  
  // Determine relationship to bet
  if (bet.primary_bettor === currentUser) {
    bettorLabel = 'Your Bet';
  } else if (bet.secondary_bettors?.includes(currentUser)) {
    bettorLabel = `Co-bet with ${bet.primary_bettor}`;
  } else if (bet.watchers?.includes(currentUser)) {
    bettorLabel = `${bet.primary_bettor}'s Bet (Watching)`;
  }
  
  // Show all bettors
  let bettorsList = bet.primary_bettor;
  if (bet.secondary_bettors?.length > 0) {
    bettorsList += ` + ${bet.secondary_bettors.join(', ')}`;
  }
  
  return `
    <div class="bet-card">
      <div class="bet-header">
        <span class="bet-label">${bettorLabel}</span>
        <span class="bettors">${bettorsList}</span>
      </div>
      <!-- rest of bet display -->
    </div>
  `;
}
```

### 3. Add Sharing UI

```javascript
// Add share button to bet cards
<button onclick="shareBet(${bet.db_id})">Share</button>

function shareBet(betId) {
  const username = prompt('Enter username to share with:');
  const role = confirm('Secondary bettor? (Cancel for watcher)') ? 'secondary' : 'watcher';
  
  fetch(`/api/bets/${betId}/share`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, role })
  })
  .then(res => res.json())
  .then(data => {
    alert(data.message);
    loadBets();  // Refresh
  });
}
```

## Migration Script

Create: `migrate_to_sharing_v2.py`

```python
#!/usr/bin/env python3
"""
Migration script: bet_users table → array columns
Run this ONCE to migrate the system
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db
from models import Bet, User, bet_users
from sqlalchemy import text

def migrate():
    with app.app_context():
        print("=== MIGRATION: Bet Sharing V2 ===\n")
        
        # Step 1: Add columns if not exist
        print("Step 1: Adding new columns...")
        try:
            db.session.execute(text("""
                ALTER TABLE bets 
                ADD COLUMN IF NOT EXISTS secondary_bettors INTEGER[] DEFAULT '{}',
                ADD COLUMN IF NOT EXISTS watchers INTEGER[] DEFAULT '{}';
            """))
            db.session.commit()
            print("✓ Columns added\n")
        except Exception as e:
            print(f"✗ Error adding columns: {e}\n")
            return
        
        # Step 2: Migrate data
        print("Step 2: Migrating bet_users data...")
        
        # Get all bets
        bets = Bet.query.all()
        migrated = 0
        
        for bet in bets:
            # Get primary bettor
            primary = db.session.execute(
                bet_users.select().where(
                    db.and_(
                        bet_users.c.bet_id == bet.id,
                        bet_users.c.is_primary_bettor == True
                    )
                )
            ).fetchone()
            
            if primary:
                bet.user_id = primary.user_id
            
            # Get secondary bettors (was viewers, now secondary)
            secondaries = db.session.execute(
                bet_users.select().where(
                    db.and_(
                        bet_users.c.bet_id == bet.id,
                        bet_users.c.is_primary_bettor == False
                    )
                )
            ).fetchall()
            
            if secondaries:
                bet.secondary_bettors = [s.user_id for s in secondaries]
            else:
                bet.secondary_bettors = []
            
            bet.watchers = []  # Empty for now
            
            migrated += 1
            
            if migrated % 10 == 0:
                print(f"  Migrated {migrated} bets...")
        
        db.session.commit()
        print(f"✓ Migrated {migrated} bets\n")
        
        # Step 3: Verify
        print("Step 3: Verifying migration...")
        
        no_primary = Bet.query.filter(Bet.user_id.is_(None)).count()
        with_secondary = Bet.query.filter(
            db.func.array_length(Bet.secondary_bettors, 1) > 0
        ).count()
        
        print(f"  Bets without primary bettor: {no_primary}")
        print(f"  Bets with secondary bettors: {with_secondary}")
        
        if no_primary > 0:
            print("\n⚠️  WARNING: Some bets have no primary bettor!")
            print("  Review before dropping bet_users table")
            return
        
        print("\n✓ Migration successful!")
        print("\nNext steps:")
        print("1. Test the application thoroughly")
        print("2. If everything works, run: DROP TABLE bet_users;")
        print("3. Update all bet creation scripts to use new methods")

if __name__ == '__main__':
    migrate()
```

## Testing Checklist

- [ ] Run migration script
- [ ] Verify all existing bets still visible to correct users
- [ ] Test adding new bet with secondary bettors
- [ ] Test adding new bet with watchers
- [ ] Test "Watched Bets" view
- [ ] Test sharing existing bet
- [ ] Test removing secondary bettor/watcher
- [ ] Verify bet card displays show correct labels
- [ ] Check that etoteja can still see manishslal's bets
- [ ] Test with 3+ users on one bet

## Rollback Plan

If issues occur:

```sql
-- Restore bet_users table from backup
-- Re-populate from new columns
INSERT INTO bet_users (bet_id, user_id, is_primary_bettor)
SELECT id, user_id, TRUE FROM bets;

INSERT INTO bet_users (bet_id, user_id, is_primary_bettor)
SELECT id, UNNEST(secondary_bettors), FALSE FROM bets
WHERE array_length(secondary_bettors, 1) > 0;

-- Remove new columns
ALTER TABLE bets 
DROP COLUMN secondary_bettors,
DROP COLUMN watchers;
```

## Benefits of New System

✅ **Clearer ownership**: user_id = primary bettor only
✅ **Distinction**: Secondary bettors (co-bets) vs watchers (just viewing)
✅ **Better UI**: Can show "Watched Bets" separately
✅ **Simpler queries**: No join needed, just array containment
✅ **Better performance**: Array containment with GIN index is fast
✅ **More flexible**: Easy to add role-specific permissions later

## Risks

⚠️ **Array columns** require PostgreSQL (already using it ✓)
⚠️ **Breaking change** - all existing code must be updated
⚠️ **Migration complexity** - must preserve all existing access
