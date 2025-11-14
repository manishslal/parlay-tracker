# Frontend to Database Mapping

## Current State (Using JSON blob)
Frontend pulls data from API endpoints which return `bet.to_dict()` that extracts from `bet_data` JSON column.

## Target State (Using Structured Tables)
API should query `bet_legs` table and construct response from relational data.

---

## Bet-Level Fields Mapping

### Frontend Parlay Object → Database Columns

| Frontend Field | Current Source | New Source | Database Table.Column |
|---|---|---|---|
| `bet_id` | `bet_data.bet_id` | Direct | `bets.bet_id` |
| `name` | `bet_data.name` | Construct | Derive from bet_type |
| `type` | `bet_data.type` | Direct | `bets.bet_type` |
| `betting_site` | `bet_data.betting_site` | Direct | `bets.betting_site` |
| `status` | `bet_data.status` | Direct | `bets.status` |
| `wager` | `bet_data.wager` | Direct | `bets.wager` |
| `odds` | `bet_data.odds` | Direct | `bets.final_odds` |
| `returns` | `bet_data.returns` | Direct | `bets.potential_winnings` |
| `bet_date` | `bet_data.bet_date` | Direct | `bets.bet_date` |
| `legs` | `bet_data.legs[]` | **Query** | `bet_legs` table (JOIN) |
| `db_id` | `bet.id` | Direct | `bets.id` |

---

## Leg-Level Fields Mapping

### Frontend Leg Object → Database Columns

| Frontend Field | Current Source | New Source | Database Table.Column |
|---|---|---|---|
| `player` | `leg.player` | Direct | `bet_legs.player_name` |
| `team` | `leg.team` | Direct | `bet_legs.player_team` |
| `position` | `leg.position` | Direct | `bet_legs.player_position` |
| `opponent` | `leg.opponent` | Construct | Derive from `home_team`/`away_team` |
| `stat` | `leg.stat` OR `leg.bet_type` | Direct | `bet_legs.bet_type` |
| `target` | `leg.target` | Direct | `bet_legs.target_value` |
| `current` | `leg.current` | Direct | `bet_legs.achieved_value` |
| `status` | `leg.status` | Direct | `bet_legs.status` |
| `gameId` | `leg.gameId` | Direct | `bet_legs.game_id` |
| `gameStatus` | ESPN API | Direct | `bet_legs.game_status` |
| `homeTeam` | Derived | Direct | `bet_legs.home_team` |
| `awayTeam` | Derived | Direct | `bet_legs.away_team` |
| `homeScore` | ESPN API | Direct | `bet_legs.home_score` |
| `awayScore` | ESPN API | Direct | `bet_legs.away_score` |

---

## Special Cases

### 1. Opponent Field Construction
```python
# If player's team is home team:
opponent = f"{away_team}"

# If player's team is away team:
opponent = f"@ {home_team}"
```

### 2. Bet Name Construction
```python
# Based on bet_type and leg count
if bet_type == 'SGP':
    name = f"{total_legs} Leg SGP"
elif bet_type == 'Parlay':
    name = f"{total_legs} Pick Parlay"
else:
    name = bet_type
```

### 3. Jersey Number Display
```python
# Can now be added to frontend
jersey_display = f"#{jersey_number}" if jersey_number else ""
# Example: "Patrick Mahomes #15"
```

---

## New API Endpoint Response Structure

### Proposed `/api/bets` endpoint response:

```json
{
  "bet_id": "DK123456789",
  "name": "5 Leg SGP",
  "type": "SGP",
  "betting_site": "DraftKings",
  "status": "pending",
  "wager": 10.00,
  "odds": 250,
  "returns": 35.00,
  "bet_date": "2024-11-08",
  "db_id": 123,
  "legs": [
    {
      "player": "Patrick Mahomes",
      "player_id": 45,
      "team": "KC",
      "jersey_number": 15,
      "position": "QB",
      "opponent": "@ LV",
      "stat": "passing_yards",
      "target": 250.0,
      "current": 0,
      "status": "pending",
      "gameId": "401234567",
      "gameStatus": "Scheduled",
      "homeTeam": "LV",
      "awayTeam": "KC",
      "homeScore": 0,
      "awayScore": 0
    }
  ]
}
```

---

## Implementation Steps

### Phase 1: Create New API Method
1. Add `to_dict_structured()` method to Bet model
2. Query `bet_legs` with JOIN to `players`
3. Construct leg objects from database rows
4. Return structured response

### Phase 2: Update Endpoints
1. Modify `/todays`, `/live`, `/historical`, `/api/archived`
2. Replace `bet.to_dict()` with `bet.to_dict_structured()`
3. Test frontend compatibility

### Phase 3: Frontend Enhancements
1. Display jersey numbers
2. Add player photos (from ESPN API)
3. Show more detailed stats

---

## Backwards Compatibility

During transition, keep both methods:
- `to_dict()` - Returns old JSON blob format
- `to_dict_structured()` - Returns from database tables

This allows gradual migration and rollback if needed.

---

## Testing Checklist

- [ ] All bet-level fields display correctly
- [ ] All leg-level fields display correctly
- [ ] Opponent formatting matches current display
- [ ] Game scores update correctly
- [ ] Status colors work (pending/live/won/lost)
- [ ] Jersey numbers display
- [ ] Team logos work
- [ ] Betting site logos work
- [ ] Historical bets load
- [ ] Live bets update
- [ ] Archive functionality works
