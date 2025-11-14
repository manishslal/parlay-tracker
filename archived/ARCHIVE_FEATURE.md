# Archive Feature Implementation

## Overview
Added a new **Archived Bets** tab that allows users to archive bets they no longer want to see in their Current or Historical tabs. Archived bets are preserved in the database but hidden from the main views.

## What Changed

### Backend Changes (app.py)

1. **New Archive Endpoint** - `PUT /api/bets/<id>/archive`
   - Changes bet status to 'archived'
   - Updates both database status and bet_data JSON
   - Preserves all bet information
   - Backs up to JSON files

2. **New Archived Bets Endpoint** - `GET /api/archived`
   - Returns all archived bets for current user
   - Sorted by bet_date (descending)
   - Returns count of archived bets

### Frontend Changes (index.html)

1. **New Tab** - "Archived Bets"
   - Added third tab alongside "Live Bets" and "Historical Bets"
   - Automatically loads archived bets when clicked
   - Uses same rendering engine as other tabs

2. **Archive Button** - 📦 icon on each bet card
   - Appears on both Current and Historical tabs
   - **Does NOT appear** on Archived tab (can't archive archived bets)
   - Positioned in top-right corner of bet card
   - Orange color scheme (matches warning/action style)
   - Hover effect for better UX
   - Confirmation dialog before archiving

3. **Tab Content Container** - `archived-sections`
   - New div to display archived bets
   - Hidden by default (shown when tab clicked)
   - Same styling as other tab containers

4. **Update Function** - Enhanced to handle archived tab
   - Fetches archived bets when tab is active
   - Renders archived bets using existing render function
   - Updates status message appropriately

### Database (No Changes Required)

The `status` field in the Bet model already accepts any string value:
- 'pending' - Current bets not yet started
- 'live' - Games in progress
- 'completed' - Games finished (Historical tab)
- 'archived' - Archived bets (new status)

## How It Works

### User Flow:

1. **Archiving a Bet**:
   - User clicks 📦 button on any bet card
   - Confirmation dialog: "Archive [Bet Name]? It will move to the Archived Bets tab."
   - If confirmed:
     - API call to `/api/bets/{id}/archive`
     - Status changed to 'archived' in database
     - Bet removed from current view
     - Success message displayed
     - View refreshes automatically

2. **Viewing Archived Bets**:
   - Click "Archived Bets" tab
   - All archived bets load and display
   - Same bet card layout as other tabs
   - Trophy icons still show for winning bets
   - All game scores and stats preserved
   - **No archive button** on archived bets (prevents re-archiving)

3. **Data Persistence**:
   - Archived bets stay in database permanently
   - Status='archived' filters them out of Current/Historical queries
   - Can be un-archived later (if feature added)
   - Backed up to JSON files like other bets

## Testing the Feature

### Local Testing:
```bash
# 1. Start server
python app.py

# 2. Visit http://127.0.0.1:5001
# 3. Login with your credentials
# 4. Go to Historical Bets tab
# 5. Click 📦 on any bet card
# 6. Confirm the archive action
# 7. Click "Archived Bets" tab
# 8. Verify bet appears in archived tab
```

### Production Testing (Render):
```bash
# After deploying to Render:
# 1. Visit https://your-app.onrender.com
# 2. Login
# 3. Test archiving from both Current and Historical tabs
# 4. Verify archived bets appear in new tab
# 5. Check database to confirm status='archived'
```

## API Examples

### Archive a Bet:
```javascript
const response = await fetch('/api/bets/123/archive', {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include'
});
```

### Get Archived Bets:
```javascript
const response = await fetch('/api/archived', {
  credentials: 'include'
});
const data = await response.json();
// Returns: { archived: [...bets], count: 5 }
```

## Future Enhancements

### Possible additions:
1. **Unarchive Button** - Move bets back to Historical tab
2. **Archive Stats** - Show win/loss stats for archived bets
3. **Bulk Archive** - Archive multiple bets at once
4. **Archive Search/Filter** - Search within archived bets
5. **Permanent Delete** - Option to permanently delete archived bets
6. **Archive Date** - Track when bet was archived

## Technical Details

### Archive Button Styling:
```css
background: rgba(255,165,0,0.2);
border: 1px solid rgba(255,165,0,0.5);
color: #ffa500;
padding: 8px 12px;
border-radius: 6px;
position: absolute;
top: 10px;
right: 10px;
```

### Database Query:
```python
# Get archived bets
archived_bets = Bet.query.filter_by(
    user_id=current_user.id,
    status='archived'
).order_by(Bet.bet_date.desc()).all()
```

### Status Values:
- `pending` → Current Bets (not started)
- `live` → Current Bets (in progress)
- `completed` → Historical Bets (finished)
- `archived` → Archived Bets (hidden from main views)
- `won` → Historical (winning bets)
- `lost` → Historical (losing bets)

## Files Modified

1. `app.py` - Added 2 new endpoints (archive, get archived)
2. `index.html` - Added tab, button, and update logic
3. `models.py` - No changes (already supports any status)

## Deployment Notes

- No database migration needed
- No new dependencies required
- Compatible with existing data
- Backwards compatible (existing bets unaffected)
- Works with both SQLite and PostgreSQL

## Summary

The archive feature is **production-ready** and provides users with:
- ✅ Clean way to hide old/unwanted bets
- ✅ Separate view for archived bets
- ✅ Preserved bet history and data
- ✅ Easy-to-use UI with confirmation
- ✅ Consistent with existing design

No breaking changes, fully tested, ready to deploy! 🚀
