#!/bin/bash

# Setup OpenClaw Cron Job for Korean Financial News
# Runs every 2 hours during market hours

echo "🕐 Setting up Korean Financial News Cron Job"
echo ""

WORKSPACE="/Users/geon/.openclaw/workspace"
SCRIPT="$WORKSPACE/scripts/korean_news_scan.sh"

# Check if script exists
if [ ! -f "$SCRIPT" ]; then
    echo "❌ Script not found: $SCRIPT"
    exit 1
fi

# Make executable
chmod +x "$SCRIPT"
chmod +x "$WORKSPACE/scripts/korean_finance_rss.py"

echo "✅ Scripts are executable"
echo ""

# Create OpenClaw cron job command
echo "📋 OpenClaw Cron Job Command:"
echo ""
echo "openclaw cron add \\"
echo "  --name 'Korean Finance News' \\"
echo "  --cron '0 8,10,12,14,16,18 * * 1-5' \\"
echo "  --message 'Run news scanner: $SCRIPT' \\"
echo "  --agent main \\"
echo "  --channel telegram \\"
echo "  --announce"
echo ""

echo "⏰ Schedule: 08:00, 10:00, 12:00, 14:00, 16:00, 18:00 (Weekdays)"
echo ""

echo "🔧 Manual test:"
echo "  $SCRIPT"
