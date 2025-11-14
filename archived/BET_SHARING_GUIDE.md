# Bet Sharing System Guide

## Overview
The parlay tracker uses a **many-to-many relationship** to share bets between multiple users. One bet can have:
- **1 Primary Bettor** (owner) - the person who placed the bet
- **Multiple Viewers** - people who can see the bet but didn't place it

## Database Structure

### bet_users Table (Association Table)
```sql
CREATE TABLE bet_users (
    bet_id INTEGER REFERENCES bets(id),
    user_id INTEGER REFERENCES users(id),
    is_primary_bettor BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (bet_id, user_id)
);
```

**Example:**
```
┌─────────┬─────────┬──────────────────┬─────────────────────┐
│ bet_id  │ user_id │ is_primary_bettor│ created_at          │
├─────────┼─────────┼──────────────────┼─────────────────────┤
│   113   │    1    │      TRUE        │ 2025-11-10 20:30:00 │  ← manishslal (owner)
│   113   │    2    │      FALSE       │ 2025-11-10 20:30:00 │  ← etoteja (viewer)
│   114   │    2    │      TRUE        │ 2025-11-10 21:00:00 │  ← etoteja (owner)
│   114   │    1    │      FALSE       │ 2025-11-10 21:00:00 │  ← manishslal (viewer)
└─────────┴─────────┴──────────────────┴─────────────────────┘
```

## How to Add a Bet with Multiple Users

### Method 1: Using the Bet.add_user() Method

```python
from models import Bet, User, db

# Step 1: Create the bet
new_bet = Bet(
    bet_id='DK123456789',
    bet_type='SGP',
    status='pending',
    bet_date='2025-11-10',
    wager=10.00,
    final_odds=250,
    potential_winnings=35.00
)
db.session.add(new_bet)
db.session.commit()

# Step 2: Add primary bettor (owner)
manishslal = User.query.filter_by(username='manishslal').first()
new_bet.add_user(manishslal, is_primary=True)

# Step 3: Add viewers (anyone else who should see this bet)
etoteja = User.query.filter_by(username='etoteja').first()
new_bet.add_user(etoteja, is_primary=False)

# You can add more viewers
jtahiliani = User.query.filter_by(username='jtahiliani').first()
new_bet.add_user(jtahiliani, is_primary=False)
```

### Method 2: Using Direct SQL (for scripts)

```python
# After creating the bet and getting its ID
bet_id = new_bet.id

# Add primary bettor
db.session.execute("""
    INSERT INTO bet_users (bet_id, user_id, is_primary_bettor)
    VALUES (:bet_id, :user_id, TRUE)
""", {'bet_id': bet_id, 'user_id': manishslal.id})

# Add viewer
db.session.execute("""
    INSERT INTO bet_users (bet_id, user_id, is_primary_bettor)
    VALUES (:bet_id, :user_id, FALSE)
""", {'bet_id': bet_id, 'user_id': etoteja.id})

db.session.commit()
```

## How Users See Bets

### Backend Query (in app.py)
```python
def get_user_bets_query(user, is_active=None, is_archived=None, status=None):
    """Get bets visible to a user (owned + shared)"""
    query = Bet.query.join(bet_users, bet_users.c.bet_id == Bet.id).filter(
        bet_users.c.user_id == user.id  # Only bets this user has access to
    )
    
    if is_active is not None:
        query = query.filter(Bet.is_active == is_active)
    if is_archived is not None:
        query = query.filter(Bet.is_archived == is_archived)
    if status:
        query = query.filter(Bet.status == status)
    
    return query
```

### What Each User Sees

**When manishslal logs in:**
```
/live endpoint → Shows all live bets where user_id = 1 in bet_users
Result:
  ✓ Bet 113 (manishslal's bet - owned)
  ✓ Bet 114 (etoteja's bet - viewing)
  ✓ Any other shared bets
```

**When etoteja logs in:**
```
/live endpoint → Shows all live bets where user_id = 2 in bet_users
Result:
  ✓ Bet 113 (manishslal's bet - viewing)
  ✓ Bet 114 (etoteja's bet - owned)
  ✓ Any other shared bets
```

## Front End Display

The API response includes `bettor` field showing who placed the bet:

```json
{
  "bet_id": "DK123456789",
  "bettor": "manishslal",
  "type": "SGP",
  "status": "pending",
  "legs": [...]
}
```

**Front end logic:**
```javascript
// If viewing your own bet
if (bet.bettor === currentUser.username) {
  showAs: "Your Bet"
}
// If viewing someone else's bet
else {
  showAs: `${bet.bettor}'s Bet`
}
```

## Useful Methods

### On Bet Object

```python
# Add a user to the bet
bet.add_user(user, is_primary=True/False)
# Returns: True if added, False if already exists

# Remove a user from the bet
bet.remove_user(user)

# Get the primary bettor's username
bet.get_primary_bettor()
# Returns: "manishslal"
```

### On User Object

```python
# Get all bets visible to this user
user.get_all_bets()
# Returns: Query of all owned + shared bets

# Get only bets where user is primary bettor
user.get_primary_bets()
# Returns: Query of only owned bets
```

## Real Example from Code

From `add_manishslal_nov10_sgp.py`:

```python
# Get users
manishslal = User.query.filter_by(username='manishslal').first()
etoteja = User.query.filter_by(username='etoteja').first()

# Create bet with 8 legs
new_bet = Bet(
    bet_id='DK638984135338309629',
    bet_type='SGP',
    status='pending',
    bet_date='2025-11-10',
    ...
)
db.session.add(new_bet)
db.session.commit()

# Add bet legs
for leg_data in legs:
    leg = BetLeg(bet_id=new_bet.id, ...)
    db.session.add(leg)

db.session.commit()

# Share with both users
new_bet.add_user(manishslal, is_primary=True)   # Owner
new_bet.add_user(etoteja, is_primary=False)      # Viewer

print(f"✅ Bet created and shared with manishslal (owner) and etoteja (viewer)")
```

## Testing

To verify a bet is properly shared:

```python
# Check who has access to bet 113
bet = Bet.query.get(113)

# Method 1: Query bet_users table
result = db.session.execute("""
    SELECT u.username, bu.is_primary_bettor
    FROM bet_users bu
    JOIN users u ON bu.user_id = u.id
    WHERE bu.bet_id = 113
""").fetchall()

for username, is_primary in result:
    role = "Owner" if is_primary else "Viewer"
    print(f"{username}: {role}")

# Method 2: Check if specific user can see it
manishslal = User.query.filter_by(username='manishslal').first()
can_see = bet in manishslal.get_all_bets().all()
print(f"manishslal can see bet: {can_see}")
```

## Summary

✅ **To share a bet with multiple users:**
1. Create the bet and save to database
2. Use `bet.add_user(user, is_primary=True)` for the owner
3. Use `bet.add_user(user, is_primary=False)` for each viewer

✅ **The system automatically:**
- Shows each user only their accessible bets
- Displays who owns each bet (`bettor` field)
- Maintains proper permissions (can't edit others' bets)

✅ **Both users see the same bet in real-time** with live updates!
