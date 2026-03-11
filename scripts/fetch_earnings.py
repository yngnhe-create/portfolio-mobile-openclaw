#!/usr/bin/env python3
"""
Fetch earnings results and post summary
Runs automatically after earnings are released
"""
import json
import subprocess
import sys
import os
import re
from datetime import datetime

MEMORY_FILE = os.path.expanduser("~/.openclaw/workspace/earnings_memory.json")

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r') as f:
            return json.load(f)
    return {}

def search_earnings_results(company):
    """Search web for earnings results"""
    query = f"{company} earnings results Q4 2026 revenue EPS"
    
    # Use web_search tool via openclaw
    result = subprocess.run(
        ["openclaw", "web", "search", "--query", query, "--count", "5"],
        capture_output=True,
        text=True
    )
    
    return result.stdout

def parse_earnings_data(search_results):
    """Parse earnings data from search results"""
    # Extract key metrics using regex patterns
    data = {
        "revenue": None,
        "eps": None,
        "eps_estimate": None,
        "revenue_estimate": None,
        "beat_miss": "Unknown",
        "guidance": None,
        "ai_highlights": None,
        "key_metrics": []
    }
    
    # Look for patterns like:
    # "EPS: $X.XX vs $X.XX expected"
    # "Revenue: $X.XB vs $X.XB expected"
    # "Beat/Miss expectations"
    
    eps_match = re.search(r'EPS[:\s]+\$?([\d.]+).*?(?:vs|versus).*?\$?([\d.]+)', search_results, re.I)
    if eps_match:
        data["eps"] = eps_match.group(1)
        data["eps_estimate"] = eps_match.group(2)
    
    rev_match = re.search(r'[Rr]evenue[:\s]+\$?([\d.]+)([BM]).*?(?:vs|versus)', search_results, re.I)
    if rev_match:
        data["revenue"] = f"${rev_match.group(1)}{rev_match.group(2)}"
    
    # Check for beat/miss
    if "beat" in search_results.lower() or "beats" in search_results.lower():
        data["beat_miss"] = "Beat"
    elif "miss" in search_results.lower() or "misses" in search_results.lower():
        data["beat_miss"] = "Miss"
    
    return data

def format_earnings_summary(company, data):
    """Format earnings summary for Telegram"""
    emoji = "🟢" if data["beat_miss"] == "Beat" else "🔴" if data["beat_miss"] == "Miss" else "⚪"
    
    msg = f"{emoji} **{company} 실적 발표**\n\n"
    
    if data["beat_miss"] != "Unknown":
        msg += f"**결과:** {data['beat_miss']} {'✅' if data['beat_miss'] == 'Beat' else '❌'}\n\n"
    
    if data["revenue"]:
        msg += f"💰 **매출:** {data['revenue']}"
        if data["revenue_estimate"]:
            msg += f" (예상: {data['revenue_estimate']})"
        msg += "\n"
    
    if data["eps"]:
        msg += f"📈 **EPS:** ${data['eps']}"
        if data["eps_estimate"]:
            msg += f" (예상: ${data['eps_estimate']})"
        msg += "\n"
    
    if data["key_metrics"]:
        msg += f"\n📊 **주요 지표:**\n"
        for metric in data["key_metrics"][:5]:
            msg += f"  • {metric}\n"
    
    if data["ai_highlights"]:
        msg += f"\n🤖 **AI 관련 하이라이트:**\n{data['ai_highlights']}\n"
    
    if data["guidance"]:
        msg += f"\n🔮 **가이던스:** {data['guidance']}\n"
    
    msg += "\n---\n"
    msg += f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')} 기준"
    
    return msg

def post_to_telegram(message):
    """Post to Telegram earnings topic"""
    subprocess.run([
        "openclaw", "message", "send",
        "--target", "earnings",
        "--message", message
    ], capture_output=True)

def main():
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--company", required=True, help="Stock ticker")
    args = parser.parse_args()
    
    company = args.company.upper()
    print(f"Fetching earnings results for {company}...")
    
    # Search for results
    search_results = search_earnings_results(company)
    
    # Parse data
    data = parse_earnings_data(search_results)
    
    # Format summary
    summary = format_earnings_summary(company, data)
    
    # Post to Telegram
    post_to_telegram(summary)
    
    print(f"✅ Posted earnings summary for {company}")

if __name__ == "__main__":
    main()
