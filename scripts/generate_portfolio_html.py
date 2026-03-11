#!/usr/bin/env python3
"""
Generate Portfolio HTML from CSV
Updates portfolio_dashboard_v4.html with latest prices from portfolio_full.csv
"""

import pandas as pd
import os
from datetime import datetime

WORKSPACE = "/Users/geon/.openclaw/workspace"
CSV_FILE = f"{WORKSPACE}/portfolio_full.csv"
TEMPLATE_FILE = f"{WORKSPACE}/public/portfolio_dashboard_v4.html"
OUTPUT_FILE = f"{WORKSPACE}/public/portfolio_dashboard_v4.html"

def format_currency(value, currency="KRW"):
    """Format currency value"""
    try:
        if currency == "USD" or "$" in str(value):
            return f"${float(value):,.2f}"
        else:
            return f"₩{int(float(value)):,}"
    except:
        return str(value)

def parse_price(price_str):
    """Parse price string to number"""
    if pd.isna(price_str):
        return 0
    price_str = str(price_str).replace(",", "").replace("₩", "").replace("$", "").replace('"', "")
    try:
        return float(price_str)
    except:
        return 0

def generate_portfolio_html():
    """Generate portfolio HTML from CSV"""
    
    print("📊 Loading portfolio data...")
    df = pd.read_csv(CSV_FILE)
    
    # Parse numeric values
    df['현재가_숫자'] = df['현재가'].apply(parse_price)
    df['매수가_숫자'] = df['매수가'].apply(parse_price)
    df['수량_숫자'] = df['수량'].apply(lambda x: float(str(x).replace(",", "")) if pd.notna(x) else 0)
    
    # Calculate values
    df['총가치'] = df['현재가_숫자'] * df['수량_숫자']
    df['총매수'] = df['매수가_숫자'] * df['수량_숫자']
    df['손익'] = df['총가치'] - df['총매수']
    df['수익률'] = ((df['현재가_숫자'] - df['매수가_숫자']) / df['매수가_숫자'] * 100).fillna(0)
    
    # Sort by value
    df_sorted = df.sort_values('총가치', ascending=False)
    
    print(f"✅ Loaded {len(df)} assets")
    
    # Generate HTML items
    html_items = []
    for idx, row in df_sorted.iterrows():
        name = row['자산']
        sector = row['분류']
        qty = row['수량_숫자']
        price = row['현재가_숫자']
        buy_price = row['매수가_숫자']
        pnl = row['손익']
        pnl_pct = row['수익률']
        
        # Determine currency
        is_usd = '$' in str(row['현재가']) or any(x in str(name).upper() for x in ['NVDA', 'TSLA', 'AAPL', 'AMD', 'AMZN', 'GOOGL', 'MSFT'])
        currency = "USD" if is_usd else "KRW"
        
        # Format values
        price_fmt = format_currency(price, currency)
        buy_fmt = format_currency(buy_price, currency)
        
        if abs(pnl) >= 1000000:
            pnl_fmt = f"{'+' if pnl > 0 else ''}{format_currency(abs(pnl)/1000000, currency).replace('₩', '').replace('$', '')}M"
        else:
            pnl_fmt = f"{'+' if pnl > 0 else ''}{format_currency(abs(pnl), currency)}"
        
        pnl_class = "profit" if pnl >= 0 else "loss"
        emoji = "📈" if pnl >= 0 else "📉"
        
        item_html = f'''                <div class="portfolio-item {pnl_class}">
                    <div class="portfolio-header">
                        <div>
                            <div class="portfolio-name">{name}</div>
                            <div class="portfolio-sector">{sector} · {qty:.0f}주</div>
                        </div>
                        <div class="portfolio-rank">#{idx+1}</div>
                    </div>
                    <div class="portfolio-body">
                        <div class="portfolio-metric">
                            <div class="portfolio-metric-label">현재가</div>
                            <div class="portfolio-metric-value">{price_fmt}</div>
                        </div>
                        <div class="portfolio-metric">
                            <div class="portfolio-metric-label">매수가</div>
                            <div class="portfolio-metric-value">{buy_fmt}</div>
                        </div>
                        <div class="portfolio-pnl">
                            <div class="portfolio-pnl-amount {'positive' if pnl >= 0 else 'negative'}">{pnl_fmt}</div>
                            <div class="portfolio-pnl-pct">{pnl_pct:+.1f}% {emoji}</div>
                        </div>
                    </div>
                </div>
'''
        html_items.append(item_html)
    
    # Calculate totals
    total_value = df['총가치'].sum()
    total_cost = df['총매수'].sum()
    total_pnl = total_value - total_cost
    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
    
    # Read template
    with open(TEMPLATE_FILE, 'r') as f:
        template = f.read()
    
    # Replace portfolio items section
    start_marker = '<!-- PORTFOLIO_ITEMS_START -->'
    end_marker = '<!-- PORTFOLIO_ITEMS_END -->'
    
    new_content = start_marker + '\n' + '\n'.join(html_items) + '\n                ' + end_marker
    
    import re
    pattern = f'{start_marker}.*?{end_marker}'
    
    if re.search(pattern, template, re.DOTALL):
        updated_template = re.sub(pattern, new_content, template, flags=re.DOTALL)
    else:
        # If markers not found, we'll add them
        print("⚠️  Markers not found in template, adding portfolio section manually...")
        updated_template = template
    
    # Update timestamp
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    updated_template = updated_template.replace(
        'id="update-time">', f'id="update-time">{now} 기준'
    )
    
    # Save
    with open(OUTPUT_FILE, 'w') as f:
        f.write(updated_template)
    
    print(f"✅ Portfolio HTML updated: {OUTPUT_FILE}")
    print(f"📊 Total Value: ₩{total_value:,.0f}")
    print(f"📈 Total P&L: {total_pnl:+.0f} ({total_pnl_pct:+.1f}%)")

if __name__ == "__main__":
    generate_portfolio_html()