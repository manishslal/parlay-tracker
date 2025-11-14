#!/bin/bash
# Sync data files from Render backend to local
# Usage: ./sync_from_remote.sh

set -e

API_BASE="https://parlay-tracker-backend.onrender.com"
ADMIN_TOKEN="mySuperSecretToken123"
DATA_DIR="./data"

echo "Syncing data files from $API_BASE..."

# Fetch all files
response=$(curl -s -H "X-Admin-Token: $ADMIN_TOKEN" "$API_BASE/admin/export_files")

# Check if response contains error
if echo "$response" | grep -q '"error"'; then
    echo "Error from server:"
    echo "$response" | python3 -m json.tool
    exit 1
fi

# Parse and save each file
echo "$response" | python3 -c "
import json
import sys

data = json.load(sys.stdin)

with open('$DATA_DIR/Live_Bets.json', 'w') as f:
    json.dump(data['live_bets'], f, indent=2)

with open('$DATA_DIR/Todays_Bets.json', 'w') as f:
    json.dump(data['todays_bets'], f, indent=2)

with open('$DATA_DIR/Historical_Bets.json', 'w') as f:
    json.dump(data['historical_bets'], f, indent=2)

print('✅ Synced all files successfully!')
print(f\"  Live: {len(data['live_bets'])} parlays\")
print(f\"  Todays: {len(data['todays_bets'])} parlays\")
print(f\"  Historical: {len(data['historical_bets'])} parlays\")
"

echo ""
echo "Files synced to $DATA_DIR/"
