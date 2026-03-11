#!/bin/bash
# Daily WiseReport Executive Summary Generator
# Runs every morning at 07:00 AM KST

echo "🌅 Daily WiseReport Update Started: $(date)"

# 1. Run scraper
cd /Users/geon/.openclaw/workspace/scripts
python3 wisereport_complete_scraper.py

# 2. Generate summary
cd /Users/geon/.openclaw/workspace
python3 scripts/generate_executive_summary.py --date=$(date +%Y-%m-%d)

# 3. Build HTML report
python3 scripts/build_command_center.py --date=$(date +%Y-%m-%d)

# 4. Deploy to Cloudflare (optional)
# cd public && wrangler pages deploy .

echo "✅ Daily update completed: $(date)"

# Send notification
echo "Today's WiseReport summary is ready!" | openclaw message send --channel telegram
