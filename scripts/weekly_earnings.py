#!/usr/bin/env python3
"""
Weekly earnings calendar search and notifier
Runs every Sunday at 6 PM KST
"""
import json
import subprocess
from datetime import datetime, timedelta
import os

# Tech/AI companies to track
DEFAULT_COMPANIES = [
    "NVDA", "MSFT", "GOOGL", "META", "AMZN", "TSLA", "AMD", 
    "AAPL", "NFLX", "CRM", "ORCL", "INTC", "QCOM", "AVGO",
    "TSM", "ASML", "SNOW", "PLTR", "CRWD", "NET"
]

MEMORY_FILE = os.path.expanduser("~/.openclaw/workspace/earnings_memory.json")

def load_memory():
    """Load tracked companies memory"""
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r') as f:
            return json.load(f)
    return {"tracked_companies": [], "last_suggestions": []}

def save_memory(memory):
    """Save tracked companies memory"""
    with open(MEMORY_FILE, 'w') as f:
        json.dump(memory, f, indent=2)

def search_earnings_calendar():
    """Search for upcoming week's earnings"""
    # This would use a financial API or web scraping
    # For now, return a mock structure
    next_week = []
    today = datetime.now()
    
    for i in range(1, 8):  # Next 7 days
        date = today + timedelta(days=i)
        # In real implementation, this would search actual earnings data
        next_week.append({
            "date": date.strftime("%Y-%m-%d"),
            "companies": []  # Would be populated from actual search
        })
    
    return next_week

def format_earnings_message(earnings_data, tracked_companies):
    """Format earnings calendar for Telegram"""
    msg = f"📊 **주간 실적 발표 일정**\n\n"
    msg += f"📅 **기간:** {datetime.now().strftime('%Y-%m-%d')} ~ {(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')}\n\n"
    
    if tracked_companies:
        msg += f"📌 **자주 추적하는 기업:** {', '.join(tracked_companies[:10])}\n\n"
    
    msg += "---\n\n"
    msg += "이번 주 발표 예정 기업이 있으면 댓글로 알려줄게.\n"
    msg += "추적하고 싶은 기업을 댓글로 답장해줘! (예: NVDA, MSFT, TSLA)"
    
    return msg

def post_to_telegram(message):
    """Post message to Telegram earnings topic"""
    # Use openclaw message command
    cmd = [
        "openclaw", "message", "send",
        "--target", "earnings",
        "--message", message
    ]
    subprocess.run(cmd, capture_output=True)

def main():
    # Load memory
    memory = load_memory()
    tracked_companies = memory.get("tracked_companies", DEFAULT_COMPANIES)
    
    # Search earnings calendar
    earnings_data = search_earnings_calendar()
    
    # Format message
    message = format_earnings_message(earnings_data, tracked_companies)
    
    # Post to Telegram
    post_to_telegram(message)
    
    # Save suggestions for this week
    memory["last_suggestions"] = tracked_companies[:10]
    save_memory(memory)
    
    print(f"✅ Weekly earnings calendar posted at {datetime.now()}")

if __name__ == "__main__":
    main()
