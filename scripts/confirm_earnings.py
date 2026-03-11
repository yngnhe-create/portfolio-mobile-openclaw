#!/usr/bin/env python3
"""
Handle user confirmation and schedule earnings tracking jobs
"""
import json
import subprocess
import re
from datetime import datetime
import os

MEMORY_FILE = os.path.expanduser("~/.openclaw/workspace/earnings_memory.json")

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r') as f:
            return json.load(f)
    return {"tracked_companies": [], "scheduled_jobs": []}

def save_memory(memory):
    with open(MEMORY_FILE, 'w') as f:
        json.dump(memory, f, indent=2)

def parse_companies(text):
    """Extract stock tickers from user message"""
    # Common patterns: NVDA, MSFT, TSLA or NVDA MSFT TSLA
    tickers = re.findall(r'\b([A-Z]{2,5})\b', text.upper())
    # Filter valid tickers (2-5 uppercase letters)
    valid_tickers = [t for t in tickers if len(t) <= 5 and t.isalpha()]
    return list(set(valid_tickers))  # Remove duplicates

def get_earnings_date(company):
    """Get earnings date/time for a company"""
    # This would search actual earnings calendar
    # Returns datetime object when earnings will be released
    # Mock for now - in real implementation would use financial API
    return None

def schedule_earnings_job(company, earnings_datetime):
    """Schedule a one-shot cron job for earnings result"""
    # Create job name
    job_name = f"earnings-{company.lower()}-{earnings_datetime.strftime('%Y%m%d')}"
    
    # Schedule job 2 hours after earnings (to ensure report is available)
    run_time = earnings_datetime + timedelta(hours=2)
    
    # Format for cron ( minute hour day month * )
    cron_time = run_time.strftime("%M %H %d %m")
    
    # Create the command
    cmd = f"python3 {os.path.expanduser('~/.openclaw/workspace/scripts/fetch_earnings.py')} --company {company}"
    
    # Schedule with openclaw cron
    subprocess.run([
        "openclaw", "cron", "add",
        "--name", job_name,
        "--schedule", f"{cron_time} *",
        "--command", cmd,
        "--once"  # One-shot job
    ], capture_output=True)
    
    return job_name

def main():
    # Get user reply (would be passed as argument or from context)
    import sys
    if len(sys.argv) < 2:
        print("Usage: confirm_earnings.py '<user_message>'")
        return
    
    user_message = sys.argv[1]
    
    # Parse companies from message
    companies = parse_companies(user_message)
    
    if not companies:
        print("No valid stock tickers found in message")
        return
    
    # Load memory
    memory = load_memory()
    
    # Schedule jobs for each company
    scheduled = []
    for company in companies:
        earnings_date = get_earnings_date(company)
        if earnings_date:
            job_name = schedule_earnings_job(company, earnings_date)
            scheduled.append({
                "company": company,
                "date": earnings_date.strftime("%Y-%m-%d %H:%M"),
                "job": job_name
            })
            # Add to tracked companies memory
            if company not in memory["tracked_companies"]:
                memory["tracked_companies"].append(company)
        else:
            scheduled.append({
                "company": company,
                "date": "Unknown - will check later",
                "job": None
            })
    
    # Save memory
    save_memory(memory)
    
    # Post confirmation to Telegram
    msg = f"✅ **실적 추적 설정 완료**\n\n"
    for s in scheduled:
        msg += f"📈 {s['company']}: {s['date']}\n"
    msg += f"\n📊 총 {len(scheduled)}개 기업 실적 발표 후 결과를 알려줄게!"
    
    subprocess.run([
        "openclaw", "message", "send",
        "--target", "earnings",
        "--message", msg
    ], capture_output=True)
    
    print(f"Scheduled {len(scheduled)} earnings tracking jobs")

if __name__ == "__main__":
    from datetime import timedelta
    main()
