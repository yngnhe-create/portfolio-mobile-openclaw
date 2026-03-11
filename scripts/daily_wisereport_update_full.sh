#!/bin/bash
# Daily WiseReport Executive Summary Generator with Telegram
# Runs every morning at 07:00 AM KST

echo "🌅 Daily WiseReport Update Started: $(date)"

# 1. Run scraper
cd /Users/geon/.openclaw/workspace/scripts
python3 wisereport_complete_scraper.py

# 2. Generate summary
cd /Users/geon/.openclaw/workspace
python3 scripts/generate_executive_summary.py --date=$(date +%Y-%m-%d)

# 3. Generate Telegram report
python3 scripts/generate_telegram_report.py --date=$(date +%Y-%m-%d) --output=/tmp/telegram_daily.txt

# 4. Build HTML report
python3 scripts/build_command_center.py --date=$(date +%Y-%m-%d)

# 5. Deploy to Cloudflare
cd public && wrangler pages deploy . --project-name=portfolio-mobile-openclaw

# 6. Send Telegram notification (if configured)
# Note: Requires Telegram bot token and chat ID configuration
# openclaw message send --file /tmp/telegram_daily.txt --channel telegram

echo "✅ Daily update completed: $(date)"
echo "📊 Report available at: https://portfolio-mobile-openclaw.pages.dev"
