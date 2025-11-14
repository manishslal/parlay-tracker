#!/bin/bash
# Daily cron job script to update team records
# Add to crontab: 0 2 * * * /path/to/daily_team_update.sh

# Set the working directory
cd "$(dirname "$0")"

# Load environment variables (if using .env file)
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run the update script
.venv/bin/python update_team_records.py >> logs/team_updates.log 2>&1

# Log completion
echo "Team update completed at $(date)" >> logs/team_updates.log
