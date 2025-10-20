#!/bin/bash
# sync_data.sh - Sync local data files with GitHub

echo "📥 Pulling latest data from GitHub..."
git pull origin main

if [ $? -eq 0 ]; then
    echo "✅ Local files synced with GitHub"
    echo ""
    echo "Current data status:"
    echo "  Todays_Bets.json: $(cat data/Todays_Bets.json | python3 -c 'import sys, json; data=json.load(sys.stdin); print(f"{len(data)} parlays")')"
    echo "  Live_Bets.json: $(cat data/Live_Bets.json | python3 -c 'import sys, json; data=json.load(sys.stdin); print(f"{len(data)} parlays")')"
    echo "  Historical_Bets.json: $(cat data/Historical_Bets.json | python3 -c 'import sys, json; data=json.load(sys.stdin); print(f"{len(data)} parlays")')"
else
    echo "❌ Error syncing with GitHub"
    exit 1
fi
