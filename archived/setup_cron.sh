#!/bin/bash
# Setup script for team data cron job
# This will add a cron entry to run daily_team_update.sh at 2am every day

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CRON_SCRIPT="$SCRIPT_DIR/daily_team_update.sh"
CRON_ENTRY="0 2 * * * $CRON_SCRIPT"

echo "🔧 Setting up daily team data update cron job"
echo "================================================"
echo "Schedule: Every day at 2:00 AM"
echo "Script: $CRON_SCRIPT"
echo ""

# Make sure the script is executable
chmod +x "$CRON_SCRIPT"
echo "✅ Made daily_team_update.sh executable"

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"
echo "✅ Created logs directory"

# Check if cron entry already exists
if crontab -l 2>/dev/null | grep -q "$CRON_SCRIPT"; then
    echo "⚠️  Cron entry already exists"
    echo ""
    echo "Current crontab:"
    crontab -l | grep "$CRON_SCRIPT"
else
    # Add to crontab
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    echo "✅ Added cron entry to crontab"
    echo ""
    echo "Cron entry added:"
    echo "$CRON_ENTRY"
fi

echo ""
echo "================================================"
echo "✅ Setup complete!"
echo ""
echo "To verify:"
echo "  crontab -l"
echo ""
echo "To test manually:"
echo "  $CRON_SCRIPT"
echo ""
echo "To view logs:"
echo "  tail -f $SCRIPT_DIR/logs/team_updates.log"
echo ""
echo "To remove cron job:"
echo "  crontab -e  (then delete the line with daily_team_update.sh)"
