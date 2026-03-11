#!/usr/bin/env python3
"""
Update portfolio_live.html with latest CSV data
This script reads portfolio_full.csv and embeds it into the HTML
"""

import csv
import os
from datetime import datetime

WORKSPACE = "/Users/geon/.openclaw/workspace"
CSV_FILE = f"{WORKSPACE}/portfolio_full.csv"
HTML_TEMPLATE = f"{WORKSPACE}/portfolio_live.html"

def update_portfolio_html():
    """Read CSV and update HTML with latest data"""
    
    print("📊 Reading portfolio CSV...")
    
    # Read CSV
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    if not rows:
        print("❌ No data in CSV")
        return
    
    # Convert to CSV string for embedding
    csv_content = '\n'.join([','.join(row) for row in rows[:20]])  # Top 20 only
    
    # Read HTML template
    with open(HTML_TEMPLATE, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Find and replace CSV data section
    start_marker = 'const csvData = `'
    end_marker = '`;'
    
    start_idx = html.find(start_marker)
    end_idx = html.find(end_marker, start_idx + len(start_marker))
    
    if start_idx != -1 and end_idx != -1:
        new_html = html[:start_idx + len(start_marker)] + csv_content + html[end_idx:]
        
        # Update timestamp
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        new_html = new_html.replace('기준', f'{now} 기준')
        
        # Save
        with open(HTML_TEMPLATE, 'w', encoding='utf-8') as f:
            f.write(new_html)
        
        print(f"✅ Updated portfolio_live.html with {len(rows)-1} assets")
        print(f"📅 Timestamp: {now}")
    else:
        print("❌ Could not find CSV data section in HTML")

if __name__ == "__main__":
    update_portfolio_html()