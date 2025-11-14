# Parlay Tracker - Data Sync Workflow

## Understanding Data Flow

```
Local Files → GitHub → Render Backend (processes & moves parlays) → Frontend Display
                ↑
                └── Need to sync back!
```

## Important Rules

1. **Render ONLY reads from `Todays_Bets.json`** on startup
2. Render automatically moves parlays to `Live_Bets.json` or `Historical_Bets.json` based on game status
3. **Render does NOT push changes back to GitHub** (changes are lost on restart)
4. Always add new parlays to `Todays_Bets.json`, never to Live or Historical

## Workflow Scripts

### 1. Before Making Local Changes: Sync from GitHub
```bash
./sync_data.sh
```
This pulls the latest from GitHub to your local machine.

### 2. After Render Has Processed Parlays: Fetch from Render
```bash
./fetch_from_render.sh
```
This downloads the current state from Render and optionally commits it to GitHub.

### 3. If JSON Files Get Corrupted: Clean Up
```bash
python3 cleanup_json.py
```
This removes any contaminated data (like `"games"` keys added by the backend) and restores files to their original simple format.

### 4. After Adding New Parlays Locally: Push to GitHub
```bash
git add data/Todays_Bets.json
git commit -m "Add new parlay"
git push
```

## Recommended Workflow

### Adding a New Parlay
1. **Sync first**: `./sync_data.sh`
2. **Edit** `data/Todays_Bets.json` with your new parlay
3. **Validate** JSON syntax: `python3 -m json.tool data/Todays_Bets.json > /dev/null`
4. **Commit & push**:
   ```bash
   git add data/Todays_Bets.json
   git commit -m "Add [parlay name] for [date]"
   git push
   ```
5. **Wait** ~2 minutes for Render to auto-deploy
6. **Check** frontend: https://manishslal.github.io/parlay-tracker/

### Syncing After Games Complete
1. **Fetch from Render**: `./fetch_from_render.sh`
2. **Review** changes: `git diff data/`
3. **Commit** if prompted by the script

## File Purposes

- **`Todays_Bets.json`**: Add new parlays here. Render processes these on startup.
- **`Live_Bets.json`**: Auto-populated by Render when games are in progress. Don't edit manually.
- **`Historical_Bets.json`**: Auto-populated by Render when games are complete. Don't edit manually.

## Returns Calculation

### When Returns Are Calculated Automatically:
1. **On Render startup** (every time service restarts or deploys)
2. **When parlays move** from Todays → Live → Historical
3. Only calculates **missing or empty** returns (won't overwrite existing values)

### How to Manually Add Odds and Calculate Returns:
1. **Edit the JSON file** (e.g., `data/Historical_Bets.json`):
   ```json
   {
     "name": "My Parlay",
     "type": "SGP",
     "odds": "+650",
     "wager": 10,
     "returns": "",
     "betting_site": "DraftKings",
     "bet_id": "ABC123456",
     "legs": [...]
   }
   ```
2. **Push to GitHub**: `git add data/*.json && git commit -m "Add odds" && git push`
3. **Wait** ~2 minutes for Render to restart and auto-calculate
4. **Or manually trigger**: `./calculate_returns.sh`
5. **Fetch results**: `./fetch_from_render.sh`

### Parlay Fields Explained:
- **name**: Display name of the parlay
- **type**: "SGP" (Same Game Parlay), "Parlay", "Wager", etc.
- **odds**: American odds format ("+650" or "-110")
- **wager**: Amount wagered (number or string)
- **returns**: Calculated profit (auto-calculated by backend)
- **betting_site**: Name of betting platform (e.g., "DraftKings", "FanDuel")
- **bet_id**: Unique bet identifier from the betting site
- **legs**: Array of individual bet legs

### Date Format Standard:
- **Format**: `YYYY-MM-DD` (e.g., "2025-10-20")
- **Why**: Human-readable, ISO 8601 standard, consistent with Historical_Bets
- **Usage**: Used in all `game_date` fields within legs
- **Backend**: Automatically converts to YYYYMMDD for ESPN API calls
- **Legacy**: Frontend supports both formats (YYYYMMDD and YYYY-MM-DD) for backwards compatibility

### Odds Format:
- **Positive**: `"+650"` (underdog, multiply wager by 6.5)
- **Negative**: `"-110"` (favorite, divide 100 by odds)
- **Per-leg odds**: Can also add `"odds"` to individual legs for automatic calculation

### Force Recalculation:
If you want to overwrite existing returns:
```bash
./calculate_returns.sh force
```

## Troubleshooting

### "My parlay disappeared!"
- It was likely moved to Live or Historical by Render
- Run `./fetch_from_render.sh` to see where it went

### "My local changes got overwritten!"
- Always run `./sync_data.sh` before making changes
- Use `git status` to check for uncommitted changes before pulling

### "Render shows old data"
- Push your changes: `git push`
- Wait 2 minutes for auto-deploy
- Check deploy status: https://dashboard.render.com/

### "JSON files have extra 'games' data!"
- This happens when processed data (with ESPN stats) gets saved back to files
- Run `python3 cleanup_json.py` to remove contaminated data
- Files should only contain: `name`, `type`, `legs`, `odds`, `wager`, `returns`
- The backend adds `"games"` temporarily for frontend display, but it shouldn't be persisted

## Quick Reference

| Task | Command |
|------|---------|
| Pull latest from GitHub | `./sync_data.sh` |
| Download from Render backend | `./fetch_from_render.sh` |
| Check local changes | `git status` |
| Push to GitHub | `git push` |
| Force Render redeploy | `git commit --allow-empty -m "Trigger deploy" && git push` |
