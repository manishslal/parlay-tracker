#!/bin/bash
# fetch_from_render.sh - Download current parlay state from Render backend

ADMIN_TOKEN="mySuperSecretToken123"
BACKEND_URL="https://parlay-tracker-backend.onrender.com"

echo "� Fetching current state from Render backend..."

# Download each endpoint with admin token and pretty-print with Python
curl -s -H "X-Admin-Token: mySuperSecretToken123" \
  "${RENDER_URL}/todays" | python3 -m json.tool > "$DATA_DIR/Todays_Bets.json"

curl -s -H "X-Admin-Token: mySuperSecretToken123" \
  "${RENDER_URL}/live" | python3 -m json.tool > "$DATA_DIR/Live_Bets.json"

curl -s -H "X-Admin-Token: mySuperSecretToken123" \
  "${RENDER_URL}/historical" | python3 -m json.tool > "$DATA_DIR/Historical_Bets.json"

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
