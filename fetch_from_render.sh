#!/bin/bash
# fetch_from_render.sh - Download current parlay state from Render backend

ADMIN_TOKEN="mySuperSecretToken123"
BACKEND_URL="https://parlay-tracker-backend.onrender.com"

echo "📥 Fetching current parlay state from Render..."

# Fetch all three endpoints
echo "Fetching Todays Bets..."
curl -s -H "X-Admin-Token: $ADMIN_TOKEN" "$BACKEND_URL/todays" > data/Todays_Bets.json

echo "Fetching Live Bets..."
curl -s -H "X-Admin-Token: $ADMIN_TOKEN" "$BACKEND_URL/live" > data/Live_Bets.json

echo "Fetching Historical Bets..."
curl -s -H "X-Admin-Token: $ADMIN_TOKEN" "$BACKEND_URL/historical" > data/Historical_Bets.json

echo ""
echo "✅ Downloaded current state from Render"
echo ""
echo "Current data status:"
echo "  Todays_Bets.json: $(cat data/Todays_Bets.json | python3 -c 'import sys, json; data=json.load(sys.stdin); print(f"{len(data)} parlays")')"
echo "  Live_Bets.json: $(cat data/Live_Bets.json | python3 -c 'import sys, json; data=json.load(sys.stdin); print(f"{len(data)} parlays")')"
echo "  Historical_Bets.json: $(cat data/Historical_Bets.json | python3 -c 'import sys, json; data=json.load(sys.stdin); print(f"{len(data)} parlays")')"
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
