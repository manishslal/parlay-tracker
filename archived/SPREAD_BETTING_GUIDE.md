# Spread Betting Guide

## How to Add Spread Bets

The spread betting feature allows you to bet on teams with point spreads (e.g., Lions -7, Bucs +3.5).

### Spread Bet Format

```json
{
  "stat": "spread",
  "team": "Detroit Lions",
  "target": -7,
  "away": "Tampa Bay Buccaneers",
  "home": "Detroit Lions",
  "game_date": "2025-10-20"
}
```

### Understanding Spread Values

- **Negative spread (e.g., -7)**: Team must WIN by MORE than this amount
  - Example: Lions -7 means Lions must win by 8+ points
  - If Lions win 24-20 (only 4 points), the bet LOSES
  
- **Positive spread (e.g., +7)**: Team can LOSE by UP TO this amount and still cover
  - Example: Bucs +7 means Bucs can lose by up to 7 points
  - If Bucs lose 20-24 (only 4 points), the bet WINS
  - If Bucs lose 10-24 (14 points), the bet LOSES

### Example Parlay with Spread

```json
{
  "name": "Week 8 Spread Parlay",
  "bet_id": "123456",
  "betting_site": "FanDuel",
  "type": "Parlay",
  "wager": 20,
  "odds": "+250",
  "legs": [
    {
      "stat": "spread",
      "team": "Detroit Lions",
      "target": -7,
      "away": "Tampa Bay Buccaneers",
      "home": "Detroit Lions",
      "game_date": "2025-10-20"
    },
    {
      "stat": "spread",
      "team": "Kansas City Chiefs",
      "target": -3.5,
      "away": "Las Vegas Raiders",
      "home": "Kansas City Chiefs",
      "game_date": "2025-10-20"
    }
  ]
}
```

## Display Differences

### Spread/Moneyline Bets
- **Progress Column**: Shows score differential from team's perspective
  - Example: "Lions +15" (Lions are up by 15)
  - Example: "Bucs -7" (Bucs are down by 7)
  - Color-coded: Green for positive, red for negative

### Regular Stat Bets (Yards, TDs, etc.)
- **Progress Column**: Shows percentage bar
  - Example: "75%" with colored progress bar

## How It Works

1. The system fetches the current score from ESPN
2. Calculates score differential from the bet team's perspective
3. Checks if spread is covered:
   - For Lions -7: (Lions score - Opponent score) must be > 7
   - For Bucs +7: (Bucs score - Opponent score) must be > -7 (can lose by up to 7)
4. Displays current score differential in the Progress column
5. Shows ✅ Hit or 🚫 Miss in Status column
