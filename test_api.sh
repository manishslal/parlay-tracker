#!/bin/bash
echo "Testing Parlay Tracker Backend API..."
echo ""
echo "1. Testing /live endpoint:"
curl -s -H "X-Admin-Token: mySuperSecretToken123" https://parlay-tracker-backend.onrender.com/live | python3 -m json.tool 2>/dev/null | head -30
echo ""
echo "2. Testing /todays endpoint:"
curl -s -H "X-Admin-Token: mySuperSecretToken123" https://parlay-tracker-backend.onrender.com/todays | python3 -m json.tool 2>/dev/null | head -30
echo ""
echo "3. Testing /historical endpoint:"
curl -s -H "X-Admin-Token: mySuperSecretToken123" https://parlay-tracker-backend.onrender.com/historical | python3 -m json.tool 2>/dev/null | head -30
