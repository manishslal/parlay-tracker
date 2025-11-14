# Preview: Two Bets for User JTahiliani
## Date: November 9, 2025

---

## 🎯 BET #1: NFL 2-Leg Parlay
**Wager:** $100.00  
**Type:** 2 Leg Parlay  
**Status:** Pending  
**Sport:** NFL  
**Net Return:** $180.37  

### Bet Metadata
```json
{
  "user": "JTahiliani",
  "user_id": <TO BE CREATED>,
  "placed_at": "2025-11-09T20:00:00",
  "wager_amount": 100.00,
  "bonus_bets_used": 100.00,
  "potential_payout": 180.37,
  "bet_type": "PARLAY",
  "parlay_type": "standard",
  "sport": "NFL",
  "status": "pending",
  "sportsbook": "FanDuel",
  "number_of_legs": 2
}
```

### Leg 1: Buffalo Bills Spread
```json
{
  "leg_order": 1,
  "bet_type": "SPREAD",
  "bet_line_type": "spread",
  "sport": "NFL",
  "parlay_sport": "NFL",
  
  // Teams
  "player_team": "Buffalo Bills",
  "home_team": "BUF",
  "away_team": "MIA",
  
  // Game Info
  "game_id": "401772771",
  "game_date": "2025-11-09",
  "game_time": "18:00:00",
  "is_home_game": true,
  
  // Bet Details
  "target_value": -6.5,
  "stat_type": "spread",
  "original_leg_odds": -142,
  "boosted_leg_odds": null,
  "final_leg_odds": -142,
  
  // Player Info (N/A for team bets)
  "player_name": "Buffalo Bills",
  "player_id": null,
  "player_position": null,
  
  // Status
  "status": "pending",
  "is_hit": null,
  "achieved_value": null,
  "game_status": "scheduled"
}
```

### Leg 2: Detroit Lions Spread
```json
{
  "leg_order": 2,
  "bet_type": "SPREAD",
  "bet_line_type": "spread",
  "sport": "NFL",
  "parlay_sport": "NFL",
  
  // Teams
  "player_team": "Detroit Lions",
  "home_team": "DET",
  "away_team": "WSH",
  
  // Game Info
  "game_id": "401772878",
  "game_date": "2025-11-09",
  "game_time": "21:25:00",
  "is_home_game": true,
  
  // Bet Details
  "target_value": -6.5,
  "stat_type": "spread",
  "original_leg_odds": -155,
  "boosted_leg_odds": null,
  "final_leg_odds": -155,
  
  // Player Info (N/A for team bets)
  "player_name": "Detroit Lions",
  "player_id": null,
  "player_position": null,
  
  // Status
  "status": "pending",
  "is_hit": null,
  "achieved_value": null,
  "game_status": "scheduled"
}
```

---

## 🎯 BET #2: Same Game Parlay + (NBA/NFL Mixed)
**Wager:** $100.00  
**Type:** Same Game Parlay +  
**Status:** Pending  
**Sports:** NFL, NBA  
**Net Return:** $136.96  

### Bet Metadata
```json
{
  "user": "JTahiliani",
  "user_id": <TO BE CREATED>,
  "placed_at": "2025-11-09T20:00:00",
  "wager_amount": 100.00,
  "bonus_bets_used": 100.00,
  "potential_payout": 136.96,
  "bet_type": "SAME_GAME_PARLAY_PLUS",
  "parlay_type": "same_game_plus",
  "sport": "MULTI",
  "status": "pending",
  "sportsbook": "FanDuel",
  "number_of_legs": 4
}
```

### Leg 1: Same Game Parlay (DET vs WAS)
**Note:** This is a nested parlay within the main bet containing 2 sub-legs

#### Sub-leg 1a: Jahmyr Gibbs Rush + Rec Yards
```json
{
  "leg_order": 1,
  "bet_type": "PLAYER_PROP",
  "bet_line_type": "rush_rec_yards",
  "sport": "NFL",
  "parlay_sport": "NFL",
  
  // Player Info
  "player_name": "Jahmyr Gibbs",
  "player_id": <TO BE LOOKED UP>,
  "player_team": "Detroit Lions",
  "player_position": "RB",
  
  // Teams
  "home_team": "DET",
  "away_team": "WSH",
  
  // Game Info
  "game_id": "401772878",
  "game_date": "2025-11-09",
  "game_time": "21:25:00",
  "is_home_game": true,
  
  // Bet Details
  "target_value": 75.0,
  "stat_type": "rush_rec_yards",
  "original_leg_odds": -175,
  "boosted_leg_odds": null,
  "final_leg_odds": -175,
  
  // Status
  "status": "pending",
  "is_hit": null,
  "achieved_value": null,
  "game_status": "scheduled"
}
```

#### Sub-leg 1b: Detroit Lions Spread
```json
{
  "leg_order": 2,
  "bet_type": "SPREAD",
  "bet_line_type": "spread",
  "sport": "NFL",
  "parlay_sport": "NFL",
  
  // Teams
  "player_team": "Detroit Lions",
  "home_team": "DET",
  "away_team": "WSH",
  
  // Game Info
  "game_id": "401772878",
  "game_date": "2025-11-09",
  "game_time": "21:25:00",
  "is_home_game": true,
  
  // Bet Details
  "target_value": -2.5,
  "stat_type": "spread",
  "original_leg_odds": null,
  "boosted_leg_odds": null,
  "final_leg_odds": null,
  
  // Player Info (N/A for team bets)
  "player_name": "Detroit Lions",
  "player_id": null,
  "player_position": null,
  
  // Status
  "status": "pending",
  "is_hit": null,
  "achieved_value": null,
  "game_status": "scheduled"
}
```

### Leg 2: Buffalo Bills Spread (BUF vs MIA)
```json
{
  "leg_order": 3,
  "bet_type": "SPREAD",
  "bet_line_type": "spread",
  "sport": "NFL",
  "parlay_sport": "NFL",
  
  // Teams
  "player_team": "Buffalo Bills",
  "home_team": "BUF",
  "away_team": "MIA",
  
  // Game Info
  "game_id": "401772771",
  "game_date": "2025-11-09",
  "game_time": "18:00:00",
  "is_home_game": true,
  
  // Bet Details
  "target_value": -2.5,
  "stat_type": "spread",
  "original_leg_odds": -375,
  "boosted_leg_odds": null,
  "final_leg_odds": -375,
  
  // Player Info (N/A for team bets)
  "player_name": "Buffalo Bills",
  "player_id": null,
  "player_position": null,
  
  // Status
  "status": "pending",
  "is_hit": null,
  "achieved_value": null,
  "game_status": "scheduled"
}
```

### Leg 3: OKC Thunder Moneyline (OKC vs MEM)
```json
{
  "leg_order": 4,
  "bet_type": "MONEYLINE",
  "bet_line_type": "moneyline",
  "sport": "NBA",
  "parlay_sport": "NBA",
  
  // Teams
  "player_team": "Oklahoma City Thunder",
  "home_team": "OKC",
  "away_team": "MEM",
  
  // Game Info
  "game_id": "401810049",
  "game_date": "2025-11-09",
  "game_time": "23:00:00",
  "is_home_game": true,
  
  // Bet Details
  "target_value": 1.0,
  "stat_type": "moneyline",
  "original_leg_odds": -525,
  "boosted_leg_odds": null,
  "final_leg_odds": -525,
  
  // Player Info (N/A for team bets)
  "player_name": "Oklahoma City Thunder",
  "player_id": null,
  "player_position": null,
  
  // Status
  "status": "pending",
  "is_hit": null,
  "achieved_value": null,
  "game_status": "scheduled",
  
  // Special flags
  "early_payout": true
}
```

---

## 📋 Data Requirements Summary

### User Creation
- **Username:** JTahiliani
- **Display Name:** J Tahiliani (or full name)
- **Email:** <need to get from user>
- **Password:** <need to set>

### Player Lookups Required
1. **Jahmyr Gibbs** (Detroit Lions, RB)
   - ESPN Player ID
   - Current stats
   - Position confirmation

### Teams (Already in DB ✅)
- Buffalo Bills (BUF, NFL)
- Miami Dolphins (MIA, NFL)
- Detroit Lions (DET, NFL)
- Washington Commanders (WSH, NFL)
- Oklahoma City Thunder (OKC, NBA)
- Memphis Grizzlies (MEM, NBA)

### Game IDs (Retrieved ✅)
- **401772771**: BUF vs MIA (Nov 9, 18:00 UTC)
- **401772878**: DET vs WAS (Nov 9, 21:25 UTC)
- **401810049**: OKC vs MEM (Nov 9, 23:00 UTC)

### Additional Fields for Live Tracking
- **Current Scores:** Will update from ESPN API during games
- **Game Status:** Pre-game → In Progress → Final
- **Quarter/Time Remaining:** Live game state
- **Player Stats:** Real-time updates for Jahmyr Gibbs
- **Weather:** For NFL games
- **Injury Status:** Check before/during games

---

## 🔄 API Integration Points

### For Live Tracking (app.py routes needed):
1. **Game Status Updates**: Poll ESPN every 30-60 seconds during games
2. **Player Stats Updates**: Fetch Jahmyr Gibbs rush+rec yards
3. **Score Updates**: Update home_score/away_score for spread calculations
4. **Spread Calculations**: Calculate if team is covering spread in real-time
5. **Moneyline Status**: Simple win/loss for OKC

### Database Triggers:
- Auto-update `achieved_value` when game completes
- Auto-calculate `is_hit` based on achieved vs target
- Auto-update bet `status` when all legs resolve
- Send notifications on bet completion

---

## ⚠️ Special Considerations

1. **Same Game Parlay Structure**: 
   - Bet 2 has a nested parlay (legs 1a + 1b from same game)
   - May need special handling in UI/database

2. **Multi-Sport Parlay**:
   - Bet 2 mixes NFL and NBA
   - Need to track different game times/statuses

3. **Early Payout**:
   - OKC Thunder moneyline shows "EARLY PAYOUT" flag
   - May resolve early if OKC gets big lead

4. **Bonus Bets**:
   - Both bets use $100 bonus bets
   - Track separately from cash wagers

5. **Time Zones**:
   - All times in UTC from ESPN
   - Convert to EST for display (Q1 15:00 = 3:00 PM EST)

---

## ✅ Ready to Add?

Once you confirm:
1. I'll create the JTahiliani user
2. Look up Jahmyr Gibbs player info
3. Create both bets with all legs
4. Link to ESPN APIs for live tracking
5. Test the live bet view updates

**What additional information do you need, or should I proceed with adding these bets?**
