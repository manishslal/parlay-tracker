#!/bin/bash
# Manual sync using existing endpoints (workaround until /admin/export_files deploys)
TOKEN="mySuperSecretToken123"
API="https://parlay-tracker-backend.onrender.com"

echo "Downloading Live_Bets.json..."
curl -s -H "X-Admin-Token: $TOKEN" "$API/live" | python3 -c "
import json, sys
data = json.load(sys.stdin)
# Remove 'games' key from each parlay
for p in data:
    p.pop('games', None)
with open('./data/Live_Bets.json', 'w') as f:
    json.dump(data, f, indent=2)
print(f'✅ Live: {len(data)} parlays')
"

echo "Downloading Todays_Bets.json..."
curl -s -H "X-Admin-Token: $TOKEN" "$API/todays" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for p in data:
    p.pop('games', None)
with open('./data/Todays_Bets.json', 'w') as f:
    json.dump(data, f, indent=2)
print(f'✅ Todays: {len(data)} parlays')
"

echo "Downloading Historical_Bets.json..."
curl -s -H "X-Admin-Token: $TOKEN" "$API/historical" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for p in data:
    p.pop('games', None)
with open('./data/Historical_Bets.json', 'w') as f:
    json.dump(data, f, indent=2)
print(f'✅ Historical: {len(data)} parlays')
"

echo ""
echo "All files synced!"
echo ""
echo "Would you like to commit these changes to GitHub? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    git add data/*.json
    git commit -m "Sync: Update local files with Render backend state"
    git push
    echo "✅ Changes pushed to GitHub"
else
    echo "⏸️  Changes not committed. Run 'git status' to see what changed."
fi
