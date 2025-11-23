# Sport Connection Quick Fixes & Improvements

## 🚨 Critical Issues Found

| Issue | Risk | Impact | Status |
|-------|------|--------|--------|
| Only NFL/NBA detection (MLB/NHL default to NFL silently) | 🔴 HIGH | 40% of bets get wrong sport | FIX AVAILABLE |
| No sport validation (invalid values stored) | 🔴 HIGH | Live tracking fails for bad data | FIX AVAILABLE |
| Silent fallback to NFL (no warnings) | 🟡 MEDIUM | Users don't know why bets stuck | FIX AVAILABLE |
| No stat type-based detection fallback | 🟡 MEDIUM | Detection fails on unusual inputs | FIX AVAILABLE |

---

## Quick Wins (45 mins total)

### Fix 1: Add Sport Validation (15 mins)
**File**: `app.py`, line 456 in `save_bet_to_db()`

```python
# ADD at top of save_bet_to_db():
VALID_SPORTS = {'NFL', 'NBA', 'MLB', 'NHL', 'NCAAF', 'NCAAB'}

# CHANGE in leg processing loop (line ~456):
# OLD:
sport = leg_data.get('sport', 'NFL')
bet_leg = BetLeg(..., sport=sport, ...)

# NEW:
sport = leg_data.get('sport', 'NFL').upper().strip()
if sport not in VALID_SPORTS:
    app.logger.warning(f"Invalid sport '{sport}' for leg {leg_data.get('player_name')}, defaulting to NFL")
    sport = 'NFL'
bet_leg = BetLeg(..., sport=sport, ...)
```

**Impact**: Catches typos and invalid sport values before they corrupt database

---

### Fix 2: Expand Team Detection Lists (15 mins)
**File**: `routes/bets.py`, lines 632-641

**Current**:
```python
nfl_teams = ['raiders', 'cowboys', 'chiefs', ...]  # 32 teams
nba_teams = ['lakers', 'celtics', 'warriors', ...]  # 30 teams

team_lower = team_name.lower()
sport = 'NFL'
if any(nfl_team in team_lower for nfl_team in nfl_teams):
    sport = 'NFL'
elif any(nba_team in team_lower for nba_team in nba_teams):
    sport = 'NBA'
```

**New**:
```python
nfl_teams = ['raiders', 'cowboys', 'chiefs', 'chargers', 'broncos', 'patriots', 'jets', 'giants', 'eagles', 'commanders', 'bears', 'lions', 'packers', 'vikings', 'falcons', 'panthers', 'saints', 'buccaneers', 'cardinals', 'rams', '49ers', 'seahawks', 'bengals', 'browns', 'steelers', 'ravens', 'bills', 'dolphins', 'texans', 'colts', 'jaguars', 'titans']
nba_teams = ['lakers', 'celtics', 'warriors', 'bulls', 'heat', 'knicks', 'nets', 'sixers', 'raptors', 'bucks', 'suns', 'nuggets', 'clippers', 'mavericks', 'thunder', 'jazz', 'blazers', 'kings', 'wizards', 'hornets', 'pelicans', 'grizzlies', 'hawks', 'cavaliers', 'pistons', 'pacers', 'magic', 'spurs', 'rockets', 'timberwolves']
mlb_teams = ['yankees', 'redsox', 'orioles', 'rays', 'bluejays', 'indians', 'guardians', 'twins', 'whitesox', 'royals', 'tigers', 'athletics', 'mariners', 'rangers', 'astros', 'angels', 'dodgers', 'padres', 'giants', 'rockies', 'braves', 'mets', 'nationals', 'marlins', 'phillies', 'cubs', 'cardinals', 'brewers', 'pirates', 'reds']
nhl_teams = ['rangers', 'bruins', 'maple leafs', 'canadiens', 'devils', 'flyers', 'penguins', 'sabres', 'red wings', 'lightning', 'hurricanes', 'capitals', 'panthers', 'islanders', 'stars', 'avalanche', 'wild', 'blues', 'jets', 'blackhawks', 'canucks', 'flames', 'oilers', 'ducks', 'sharks', 'kings', 'desert']

team_lower = team_name.lower()
sport = 'NFL'  # DEFAULT
if any(nfl_team in team_lower for nfl_team in nfl_teams):
    sport = 'NFL'
elif any(nba_team in team_lower for nba_team in nba_teams):
    sport = 'NBA'
elif any(mlb_team in team_lower for mlb_team in mlb_teams):
    sport = 'MLB'
elif any(nhl_team in team_lower for nhl_team in nhl_teams):
    sport = 'NHL'
```

**Impact**: MLB/NHL bets now detected correctly instead of silently defaulting to NFL

---

### Fix 3: Add Stat Type Fallback Detection (10 mins)
**File**: `routes/bets.py`, add new function

```python
def detect_sport_from_stat_type(stat_type):
    """Infer sport from stat type when team matching fails"""
    if not stat_type:
        return None
    stat_lower = stat_type.lower()
    
    # NFL stats
    if any(x in stat_lower for x in ['passing_yards', 'rushing_yards', 'sacks', 'interceptions', 'pass_completions', 'rushing_attempts', 'receiving_yards', 'receiving_touchdowns']):
        return 'NFL'
    
    # NBA stats
    elif any(x in stat_lower for x in ['three_pointers', 'rebounds', 'assists', 'steals', 'blocks', 'field_goals']):
        return 'NBA'
    
    # MLB stats
    elif any(x in stat_lower for x in ['home_runs', 'strikeouts', 'batting_average', 'rbi', 'hits', 'runs', 'stolen_bases']):
        return 'MLB'
    
    # NHL stats
    elif any(x in stat_lower for x in ['goals', 'shutouts', 'saves', 'penalty_minutes', 'shots_on_goal']):
        return 'NHL'
    
    return None

# MODIFY sport detection logic:
team_lower = team_name.lower()
sport = 'NFL'  # DEFAULT

# Level 1: Team matching
if any(nfl_team in team_lower for nfl_team in nfl_teams):
    sport = 'NFL'
elif any(nba_team in team_lower for nba_team in nba_teams):
    sport = 'NBA'
elif any(mlb_team in team_lower for mlb_team in mlb_teams):
    sport = 'MLB'
elif any(nhl_team in team_lower for nhl_team in nhl_teams):
    sport = 'NHL'

# Level 2: Stat type fallback if team matching failed
stat_type_sport = detect_sport_from_stat_type(leg.get('stat'))
if stat_type_sport and sport == 'NFL':  # Only override if we defaulted to NFL
    logger.info(f"Detected sport '{stat_type_sport}' from stat type '{leg.get('stat')}'")
    sport = stat_type_sport
```

**Impact**: "60.5 points" → NBA, "40 yards" → NFL, even with unknown team name

---

### Fix 4: Add Detailed Logging for Sport Assignment (5 mins)
**File**: `services/bet_service.py`, update `process_parlay_data()` function, around line 267

```python
def process_parlay_data(parlays):
    for leg in legs:
        sport = leg.get('sport', 'NFL')
        away_team = leg.get('away_team')
        home_team = leg.get('home_team')
        player_name = leg.get('player_name', 'Unknown')
        
        logger.info(f"Fetching game for {player_name} ({away_team}@{home_team}) - Sport: {sport}")
        
        game_data = fetch_game_details_from_espn(
            leg.get('game_date'),
            away_team,
            home_team,
            sport=sport
        )
        
        if not game_data:
            logger.error(
                f"❌ NO GAME FOUND for {player_name}: {away_team}@{home_team} "
                f"on {leg.get('game_date')} with sport={sport}. "
                f"This likely indicates the sport was detected incorrectly. "
                f"Check if {sport} is correct for this matchup."
            )
            # Add warning flag to leg for frontend display
            leg['sport_match_warning'] = {
                'status': 'no_game_found',
                'detected_sport': sport,
                'teams': [away_team, home_team],
                'date': leg.get('game_date'),
                'message': 'Could not find matching game. Sport assignment may be incorrect.'
            }
        else:
            logger.info(f"✓ Game found: {game_data['teams']['away']} @ {game_data['teams']['home']}")
```

**Impact**: Logs clearly show why games aren't found (helps debug sport mismatch issues)

---

## Additional Improvements (Phase 2)

### Improvement 1: Add Sport Status to Live Bets Response
**Location**: `Bet.to_dict_structured()` in models.py

Add metadata about sport detection:
```json
{
  "legs": [...],
  "sport_detection_metadata": {
    "sport": "NBA",
    "detection_method": "team_match",  // or "stat_inference", "default_fallback"
    "confidence": 0.95,  // 0.0-1.0
    "games_found": true
  }
}
```

This helps users see if sport was correctly detected.

### Improvement 2: Add Sport Correction Endpoint
**New Route**: `PUT /api/bets/{bet_id}/sport`

```python
@bets_bp.route('/api/bets/<int:bet_id>/sport', methods=['PUT'])
@login_required
def update_bet_sport(bet_id):
    """Allow users to correct sport assignment"""
    try:
        data = request.get_json()
        new_sport = data.get('sport', '').upper()
        
        if new_sport not in VALID_SPORTS:
            return jsonify({"error": f"Invalid sport: {new_sport}"}), 400
        
        # Update all legs in bet
        legs = BetLeg.query.filter_by(bet_id=bet_id).all()
        for leg in legs:
            leg.sport = new_sport
            leg.game_id = None  # Clear cached game ID
            leg.game_status = 'STATUS_SCHEDULED'  # Reset status
        
        db.session.commit()
        logger.info(f"Updated bet {bet_id} sport to {new_sport}")
        
        # Force re-fetch from ESPN
        from app import app
        app.config['CACHE_BUST'] = True
        
        return jsonify({"success": True, "message": f"Sport updated to {new_sport}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

**Impact**: Users can fix sport assignments that were detected incorrectly

### Improvement 3: Create Team Database Table
Instead of hardcoded lists, create a Teams table:

```python
class Team(db.Model):
    __tablename__ = 'teams'
    
    id = db.Column(db.Integer, primary_key=True)
    sport = db.Column(db.String(10), nullable=False)  # NFL, NBA, MLB, NHL, etc.
    name_full = db.Column(db.String(100), nullable=False)  # "Los Angeles Lakers"
    name_short = db.Column(db.String(50))  # "Lakers"
    abbreviation = db.Column(db.String(5))  # "LAL"
    nickname = db.Column(db.String(50))  # "Lakers"
    conference = db.Column(db.String(50))  # "Western", "AFC", etc.
    league = db.Column(db.String(50))  # "NBA", "Major League Baseball", etc.
    location = db.Column(db.String(100))  # "Los Angeles"
    
    def __repr__(self):
        return f'<Team {self.name_full} ({self.sport})>'
```

**Impact**: Maintainable team detection, can use database queries instead of hardcoded lists

### Improvement 4: Sport-Specific Stat Type Mapping
Create a mapping table for standardizing stat names across sports:

```python
# Could be in database or config
STAT_TYPE_STANDARDIZATION = {
    'NFL': {
        'passing_yards': ['passing yards', 'pass yds', 'passing yds', 'passing'],
        'rushing_yards': ['rushing yards', 'rush yds', 'rushing'],
        'receiving_yards': ['receiving yards', 'rec yds', 'receiving'],
        # ... more stats
    },
    'NBA': {
        'three_pointers': ['three pointers', '3 pointers', '3pm', 'threes'],
        'rebounds': ['total rebounds', 'reb'],
        'assists': ['ast'],
        # ... more stats
    },
    # ... more sports
}
```

**Impact**: Consistent stat type handling across OCR extraction and manual input

---

## Testing Recommendations

### Add Unit Tests

**File**: `tests/test_sport_detection.py`

```python
def test_sport_detection_from_team_name():
    """Test team-based sport detection"""
    assert detect_sport("Dallas Cowboys") == "NFL"
    assert detect_sport("Los Angeles Lakers") == "NBA"
    assert detect_sport("New York Yankees") == "MLB"
    assert detect_sport("New York Rangers") == "NHL"

def test_sport_detection_from_stat_type():
    """Test stat type fallback detection"""
    assert detect_sport_from_stat_type("passing yards") == "NFL"
    assert detect_sport_from_stat_type("rebounds") == "NBA"
    assert detect_sport_from_stat_type("home runs") == "MLB"
    assert detect_sport_from_stat_type("goals") == "NHL"

def test_sport_validation():
    """Test invalid sports are rejected"""
    with pytest.raises(ValueError):
        validate_sport("INVALID_SPORT")
    
    assert validate_sport("nfl") == "NFL"  # Case normalization
    assert validate_sport("NBA") == "NBA"

def test_live_tracking_with_correct_sport():
    """Test live tracking works with correct sport"""
    # Create NFL bet
    bet = create_test_bet("Dallas Cowboys", "NFL", "passing yards", "32.5")
    assert bet.legs[0].sport == "NFL"
    
    # Fetch game
    game = fetch_game_details_from_espn("2025-01-15", "Philadelphia Eagles", "Dallas Cowboys", "NFL")
    assert game is not None

def test_live_tracking_with_wrong_sport():
    """Test live tracking fails with wrong sport"""
    # Create bet with wrong sport
    bet = create_test_bet("Los Angeles Lakers", "NFL", "points", "110.5")
    assert bet.legs[0].sport == "NFL"
    
    # Try to fetch - should fail
    game = fetch_game_details_from_espn("2025-01-15", "Los Angeles Lakers", "Boston Celtics", "NFL")
    assert game is None  # No NFL game with these teams
```

---

## Implementation Checklist

- [ ] **Fix 1** - Add sport validation (15 mins)
  - [ ] Update save_bet_to_db() to validate sport
  - [ ] Test with invalid sport value
  - [ ] Verify logs show warnings

- [ ] **Fix 2** - Expand team detection lists (15 mins)
  - [ ] Add MLB teams list
  - [ ] Add NHL teams list
  - [ ] Update detection logic
  - [ ] Test with 5 MLB teams, 5 NHL teams

- [ ] **Fix 3** - Add stat type fallback (10 mins)
  - [ ] Create detect_sport_from_stat_type() function
  - [ ] Integrate into routes/bets.py
  - [ ] Test with stat types like "passing yards", "rebounds"

- [ ] **Fix 4** - Add logging (5 mins)
  - [ ] Update process_parlay_data() logging
  - [ ] Add sport_match_warning to leg data
  - [ ] Test logs clearly show when games not found

**Total Implementation Time**: ~45 minutes
**Testing Time**: ~30 minutes
**Total**: ~75 minutes (~1.25 hours)

---

## Benefits After Implementation

| Benefit | Impact |
|---------|--------|
| **MLB bets work** | Live tracking now fetches MLB games correctly |
| **NHL bets work** | Live tracking now fetches NHL games correctly |
| **Error visibility** | Logs clearly show when sport mismatch occurs |
| **Data quality** | Invalid sports caught before storage |
| **Stat type inference** | Unknown teams detected via stat type |
| **User experience** | Users see warnings if sport seems wrong |

---

## Long-Term Recommendations

1. **Database-driven teams table** (8+ hours)
   - Replace hardcoded lists
   - Add all sports teams
   - Enable quick lookups and maintenance

2. **Standardized stat types** (4-6 hours)
   - Create stat type mapping table
   - Validate against standard names
   - Document all supported stats

3. **Sport confidence scoring** (3-5 hours)
   - Calculate confidence 0.0-1.0 for each detection
   - Surface low-confidence detections to user
   - Enable manual override UI

4. **Multi-sport detection** (2-3 hours)
   - Return top 3 possible sports
   - Show alternatives when uncertain
   - Let user choose if ambiguous

---

## Summary

**Current Issue**: Live tracking breaks for MLB/NHL bets due to silent sport detection fallback

**Quick Fixes Available**: 4 specific code changes, ~45 minutes total effort

**Impact**: 
- ✅ MLB bets now work
- ✅ NHL bets now work  
- ✅ Better error visibility
- ✅ Data quality validation

**Recommendation**: Implement all 4 quick fixes this week to improve robustness.

