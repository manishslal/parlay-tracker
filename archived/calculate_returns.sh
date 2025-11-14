#!/bin/bash

# Script to manually trigger returns calculation on Render backend
# Usage: ./calculate_returns.sh [force]
#   - No args: Only calculate missing returns
#   - force: Recalculate ALL returns (overwrite existing)

API_BASE="https://parlay-tracker-backend.onrender.com"
TOKEN="mySuperSecretToken123"

FORCE_MODE="${1:-false}"

if [ "$FORCE_MODE" = "force" ]; then
    FORCE_MODE="true"
else
    FORCE_MODE="false"
fi

echo "🧮 Triggering returns calculation on Render backend..."
echo "   Force mode: $FORCE_MODE"
echo ""

RESPONSE=$(curl -s -X POST \
  -H "X-Admin-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"force\": $FORCE_MODE}" \
  "${API_BASE}/admin/compute_returns")

echo "📊 Results:"
echo "$RESPONSE" | python3 -m json.tool

echo ""
echo "✅ Returns calculation complete!"
echo ""
echo "To see updated files, run: ./fetch_from_render.sh"
