#!/bin/bash
# Starting Goalie Scraper - Automated Scheduling
# Run this script to set up automated scraping every 2 hours

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH="/usr/bin/python3"
SCRAPER_PATH="$SCRIPT_DIR/src/nhl_prediction/starting_goalie_scraper.py"
LOG_DIR="$SCRIPT_DIR/logs"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Cron job configuration
CRON_JOB="0 */2 * * * cd $SCRIPT_DIR && $PYTHON_PATH $SCRAPER_PATH >> $LOG_DIR/starting_goalie_scraper.log 2>&1"

echo "=========================================="
echo "Starting Goalie Scraper - Cron Setup"
echo "=========================================="
echo ""
echo "This will set up automated scraping every 2 hours."
echo ""
echo "Cron job to be added:"
echo "$CRON_JOB"
echo ""
echo "Logs will be saved to: $LOG_DIR/starting_goalie_scraper.log"
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "starting_goalie_scraper.py"; then
    echo "⚠️  Cron job already exists!"
    echo ""
    echo "Current cron jobs:"
    crontab -l | grep "starting_goalie_scraper.py"
    echo ""
    read -p "Do you want to replace it? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborting."
        exit 0
    fi
    # Remove old job
    crontab -l | grep -v "starting_goalie_scraper.py" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo ""
echo "✅ Cron job added successfully!"
echo ""
echo "The scraper will run every 2 hours at:"
echo "  - 12:00 AM"
echo "  - 2:00 AM"
echo "  - 4:00 AM"
echo "  - 6:00 AM"
echo "  - 8:00 AM"
echo "  - 10:00 AM"
echo "  - 12:00 PM"
echo "  - 2:00 PM"
echo "  - 4:00 PM"
echo "  - 6:00 PM"
echo "  - 8:00 PM"
echo "  - 10:00 PM"
echo ""
echo "To verify:"
echo "  crontab -l"
echo ""
echo "To view logs:"
echo "  tail -f $LOG_DIR/starting_goalie_scraper.log"
echo ""
echo "To remove:"
echo "  crontab -e"
echo "  (then delete the line containing 'starting_goalie_scraper.py')"
echo ""
