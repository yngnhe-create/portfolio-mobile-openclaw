# 📊 Earnings Tracking System

## Overview
Automated earnings calendar tracking for tech/AI companies.

## How It Works

### 1. Weekly Calendar (Every Sunday 6 PM)
- Automatically searches upcoming week's earnings for tech/AI companies
- Posts calendar to Telegram "earnings" topic
- Auto-suggests companies you typically track

### 2. Your Confirmation
- Reply with tickers you want to track (e.g., "NVDA, MSFT, TSLA")
- System schedules one-shot jobs for each earnings date

### 3. Automatic Results
- After each earnings report, automatically searches results
- Formats summary with beat/miss, revenue, EPS, AI highlights
- Posts to Telegram "earnings" topic

## Default Tracked Companies
NVDA, MSFT, GOOGL, META, AMZN, TSLA, AMD, AAPL, NFLX, CRM, ORCL

## Memory File
`~/.openclaw/workspace/earnings_memory.json` stores your tracked companies and preferences.

## Commands

### Manual Run
```bash
# Weekly calendar (manual)
python3 ~/.openclaw/workspace/scripts/weekly_earnings.py

# Confirm companies (when you reply)
python3 ~/.openclaw/workspace/scripts/confirm_earnings.py "NVDA MSFT TSLA"

# Fetch results (auto-scheduled)
python3 ~/.openclaw/workspace/scripts/fetch_earnings.py --company NVDA
```

### View Cron Jobs
```bash
openclaw cron list
```

### Edit Tracked Companies
Edit `~/.openclaw/workspace/earnings_memory.json` and add companies to "tracked_companies" list.

## Example Workflow

1. **Sunday 6 PM**: Bot posts "This week's earnings: NVDA (Wed), MSFT (Thu)..."
2. **You reply**: "Track NVDA and MSFT"
3. **Confirmation**: "✅ Scheduled tracking for NVDA (Wed), MSFT (Thu)"
4. **Wednesday after earnings**: Bot posts NVDA results summary
5. **Thursday after earnings**: Bot posts MSFT results summary

## Notes
- Earnings results are fetched ~2 hours after scheduled release time
- System uses web search to find latest earnings data
- AI highlights are extracted for AI/tech companies
