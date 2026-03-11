#!/usr/bin/env python3
"""
Simple Portfolio HTML Generator
Generates complete HTML with all 57 stocks
"""

import pandas as pd
from datetime import datetime

WORKSPACE = "/Users/geon/.openclaw/workspace"
CSV_FILE = f"{WORKSPACE}/portfolio_full.csv"
OUTPUT_FILE = f"{WORKSPACE}/public/portfolio_dashboard_live.html"

def parse_price(price_str):
    if pd.isna(price_str):
        return 0
    s = str(price_str).replace(",", "").replace("₩", "").replace("$", "").replace('"', "")
    try:
        return float(s)
    except:
        return 0

def parse_asset_value(val_str):
    if pd.isna(val_str):
        return 0
    s = str(val_str).replace(",", "").replace('"', "")
    if "$" in s:
        try:
            num = float(s.replace("$", ""))
            return num * 1450
        except:
            return 0
    else:
        try:
            return float(s.replace("₩", ""))
        except:
            return 0

def format_currency(value):
    if value >= 100000000:
        return f"₩{value/100000000:.1f}억"
    elif value >= 10000:
        return f"₩{value/10000:.0f}만"
    return f"₩{value:,.0f}"

# Read CSV
df = pd.read_csv(CSV_FILE)

# Parse data
df['수량_숫자'] = df['수량'].apply(lambda x: float(str(x).replace(",", "")) if pd.notna(x) else 0)
df['현재가_숫자'] = df['현재가'].apply(parse_price)
df['매수가_숫자'] = df['매수가'].apply(parse_price)
df['현재가치'] = df['자산가치'].apply(parse_asset_value)
df['매수가치'] = df['매수가_숫자'] * df['수량_숫자']
df['손익'] = df['현재가치'] - df['매수가치']
df['수익률'] = ((df['현재가_숫자'] - df['매수가_숫자']) / df['매수가_숫자'] * 100).fillna(0)
df['is_usd'] = df.apply(lambda row: '$' in str(row['현재가']) or any(x in str(row['자산']).upper() for x in ['NVDA','TSLA','AMD','AMZN','GOOGL','MSFT','NLR','LLY','RTX','PLTR','HSAI']), axis=1)

df_sorted = df.sort_values('현재가치', ascending=False).reset_index(drop=True)

# Calculate totals
total_value = df_sorted['현재가치'].sum()
total_cost = df_sorted['매수가치'].sum()
total_pnl = total_value - total_cost
total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0

# Generate portfolio items
portfolio_items = []
for idx, row in df_sorted.iterrows():
    name = row['자산']
    sector = row['분류']
    qty = row['수량_숫자']
    price = row['현재가_숫자']
    buy_price = row['매수가_숫자']
    pnl = row['손익']
    pnl_pct = row['수익률']
    is_usd = row['is_usd']
    
    price_fmt = f"${price:,.2f}" if is_usd else f"₩{price:,.0f}"
    buy_fmt = f"${buy_price:,.2f}" if is_usd else f"₩{int(buy_price):,}"
    
    if abs(pnl) >= 1000000:
        pnl_fmt = f"{'+' if pnl > 0 else ''}{abs(pnl)/100000000:.2f}억" if abs(pnl) >= 100000000 else f"{'+' if pnl > 0 else ''}{abs(pnl)/10000:.0f}만"
    else:
        pnl_fmt = f"{'+' if pnl > 0 else ''}₩{abs(pnl):,.0f}"
    
    pnl_class = "profit" if pnl >= 0 else "loss"
    
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
                            <div class="portfolio-pnl-pct">{pnl_pct:+.1f}%</div>
                        </div>
                    </div>
                </div>'''
    portfolio_items.append(item_html)

# Sector data
sector_data = df_sorted.groupby('분류')['현재가치'].sum().sort_values(ascending=False)
sector_total = sector_data.sum()

sector_items = []
colors = ['#1d9bf0', '#00ba7c', '#ffd400', '#8b5cf6', '#f59e0b', '#ec4899', '#6b7280']
for i, (sector, value) in enumerate(sector_data.head(7).items()):
    pct = (value / sector_total * 100)
    count = len(df_sorted[df_sorted['분류'] == sector])
    color = colors[i % len(colors)]
    width = int(pct * 3)
    
    sector_items.append(f'''                    <div class="sector-item">
                        <div class="sector-color" style="background: {color};"></div>
                        <div class="sector-info">
                            <div class="sector-name">{sector}</div>
                            <div class="sector-count">{count}개 종목</div>
                        </div>
                        <div class="sector-bar-bg">
                            <div class="sector-bar-fill" style="width: {width}%; background: {color};"></div>
                        </div>
                        <div class="sector-percent">{pct:.1f}%</div>
                    </div>''')

# Sub-sector items
subsector_items = [
    ('🤖 AI/반도체', '삼성전자, NVDA, AMD, TIGER AI ETFs', '~19.6%'),
    ('⚡ AI 전력/인프라', 'SOL 미국AI전력, TIGER 코리아AI전력', '~11.5%'),
    ('🚗 자동차/모빌리티', '현대차, 기아, TSLA, 샤오미', '~6.5%'),
    ('🔋 배터리/2차전지', '삼성SDI, LG에너지, 포스코퓨처엠', '~5.3%'),
    ('🏢 리츠/부동산', 'ESR, 코람코, SK리츠, 신한서부, 이지스', '~5.8%'),
    ('💊 바이오/헬스케어', '파마리서치, 한미약품, 유한양행, LLY', '~2.1%'),
    ('📱 IT/플랫폼', '네이버, AMZN, GOOGL, MSFT, PLTR', '~2.3%'),
    ('₿ 가상자산', 'BTC, ETH, SOL, LINK', '~10.0%'),
    ('📈 채권/ETF', 'TIGER 고배당, KODEX 국채, 다양한 ETF', '~12.8%'),
]

subsector_html = ''.join([f'''                <div class="sector-item">
                    <div class="sector-info">
                        <div class="sector-name">{name}</div>
                        <div class="sector-count">{stocks}</div>
                    </div>
                    <div class="sector-percent">{pct}</div>
                </div>''' for name, stocks, pct in subsector_items])

now = datetime.now().strftime('%Y년 %m월 %d일 %H:%M')

# Full HTML
html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="theme-color" content="#0f1419">
    <title>📊 올인원 포트폴리오 대시보드</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #0f1419;
            --bg-secondary: #15202b;
            --bg-card: #1e2732;
            --bg-elevated: #263340;
            --text-primary: #e7e9ea;
            --text-secondary: #71767b;
            --accent-blue: #1d9bf0;
            --accent-green: #00ba7c;
            --accent-red: #f4212e;
            --accent-yellow: #ffd400;
            --border-color: #2f3336;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
        html {{ font-size: 16px; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.5;
            padding-bottom: 100px;
        }}
        .header {{
            background: linear-gradient(135deg, #1d9bf0 0%, #8b5cf6 100%);
            padding: 24px 20px;
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        .header-title {{ font-size: 1.5rem; font-weight: 800; margin-bottom: 4px; }}
        .header-subtitle {{ font-size: 0.875rem; opacity: 0.9; }}
        .update-time {{ font-size: 0.75rem; opacity: 0.85; margin-top: 10px; }}
        .nav-tabs {{
            display: flex;
            gap: 8px;
            padding: 12px 16px;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            overflow-x: auto;
            scrollbar-width: none;
        }}
        .nav-tabs::-webkit-scrollbar {{ display: none; }}
        .nav-tab {{
            flex-shrink: 0;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 600;
            background: var(--bg-card);
            color: var(--text-secondary);
            border: none;
            cursor: pointer;
            white-space: nowrap;
        }}
        .nav-tab.active {{
            background: var(--accent-blue);
            color: white;
        }}
        .container {{ padding: 16px; max-width: 600px; margin: 0 auto; }}
        .section {{ display: none; }}
        .section.active {{ display: block; }}
        .card {{
            background: var(--bg-card);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 16px;
            border: 1px solid var(--border-color);
        }}
        .card-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
        }}
        .card-title {{ font-size: 1.125rem; font-weight: 700; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-bottom: 16px;
        }}
        .stat-card {{
            background: var(--bg-card);
            border-radius: 12px;
            padding: 16px;
            border: 1px solid var(--border-color);
        }}
        .stat-value {{ font-size: 1.25rem; font-weight: 700; margin-bottom: 4px; }}
        .stat-label {{ font-size: 0.75rem; color: var(--text-secondary); }}
        .positive {{ color: var(--accent-green); }}
        .negative {{ color: var(--accent-red); }}
        
        .portfolio-item {{
            background: var(--bg-elevated);
            border-radius: 12px;
            padding: 12px;
            margin-bottom: 8px;
            border-left: 4px solid var(--accent-green);
        }}
        .portfolio-item.loss {{ border-left-color: var(--accent-red); }}
        .portfolio-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 8px;
        }}
        .portfolio-name {{ font-size: 0.95rem; font-weight: 700; }}
        .portfolio-sector {{ font-size: 0.7rem; color: var(--text-secondary); margin-top: 2px; }}
        .portfolio-rank {{
            background: var(--accent-blue);
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.65rem;
            font-weight: 700;
        }}
        .portfolio-body {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 8px;
        }}
        .portfolio-metric {{ text-align: center; }}
        .portfolio-metric-label {{ font-size: 0.6rem; color: var(--text-secondary); margin-bottom: 2px; }}
        .portfolio-metric-value {{ font-size: 0.8rem; font-weight: 600; }}
        .portfolio-pnl {{ text-align: center; }}
        .portfolio-pnl-amount {{ font-size: 0.8rem; font-weight: 700; }}
        .portfolio-pnl-pct {{ font-size: 0.65rem; color: var(--text-secondary); margin-top: 2px; }}
        
        .sector-item {{
            display: flex;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid var(--border-color);
        }}
        .sector-item:last-child {{ border-bottom: none; }}
        .sector-color {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 10px;
        }}
        .sector-info {{ flex: 1; }}
        .sector-name {{ font-size: 0.85rem; font-weight: 600; }}
        .sector-count {{ font-size: 0.7rem; color: var(--text-secondary); }}
        .sector-bar-bg {{
            flex: 1;
            height: 5px;
            background: var(--bg-primary);
            border-radius: 3px;
            margin: 0 10px;
            overflow: hidden;
        }}
        .sector-bar-fill {{ height: 100%; border-radius: 3px; }}
        .sector-percent {{ font-size: 0.8rem; font-weight: 600; min-width: 40px; text-align: right; }}
        
        .bottom-nav {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: var(--bg-secondary);
            border-top: 1px solid var(--border-color);
            padding: 10px 20px calc(10px + env(safe-area-inset-bottom));
            display: flex;
            justify-content: space-around;
            z-index: 100;
        }}
        .nav-item {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 2px;
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 0.6rem;
            background: none;
            border: none;
            cursor: pointer;
        }}
        .nav-item.active {{ color: var(--accent-blue); }}
        .nav-icon {{ font-size: 1.3rem; }}
    </style>
</head>
<body>
    <header class="header">
        <h1 class="header-title">📊 올인원 포트폴리오 대시보드</h1>
        <p class="header-subtitle">손익분석 · 섹터별 비중 · 실시간 시세</p>
        <p class="update-time">⏱️ {now} 기준</p>
    </header>

    <nav class="nav-tabs">
        <button class="nav-tab active" onclick="showSection('overview')">📈 개요</button>
        <button class="nav-tab" onclick="showSection('stocks')">📋 종목</button>
        <button class="nav-tab" onclick="showSection('sectors')">📊 섹터</button>
        <button class="nav-tab" onclick="showSection('subsectors')">🔍 세부</button>
    </nav>

    <div class="container">
        <!-- Section 1: Overview -->
        <div id="overview" class="section active">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{format_currency(total_value)}</div>
                    <div class="stat-label">총 자산</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value {'positive' if total_pnl >= 0 else 'negative'}">
                        {format_currency(abs(total_pnl))}
                    </div>
                    <div class="stat-label">총 손익 ({total_pnl_pct:+.1f}%)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(df_sorted)}</div>
                    <div class="stat-label">보유 종목</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(sector_data)}</div>
                    <div class="stat-label">섹터 분산</div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">🏆 TOP 10 보유종목</h2>
                </div>
                {''.join(portfolio_items[:10])}
            </div>
        </div>

        <!-- Section 2: All Stocks -->
        <div id="stocks" class="section">
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">📋 전체 보유종목 ({len(df_sorted)}개)</h2>
                </div>
                {''.join(portfolio_items)}
            </div>
        </div>

        <!-- Section 3: Sectors -->
        <div id="sectors" class="section">
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">📊 섹터별 비중</h2>
                </div>
                <div style="margin-top: 16px;">
                    {''.join(sector_items)}
                </div>
            </div>
        </div>

        <!-- Section 4: Sub-sectors -->
        <div id="subsectors" class="section">
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">🔍 세부 섹터 분석</h2>
                </div>
                {subsector_html}
            </div>
        </div>
    </div>

    <nav class="bottom-nav">
        <button class="nav-item active" onclick="showSection('overview')">
            <span class="nav-icon">📈</span>
            <span>개요</span>
        </button>
        <button class="nav-item" onclick="showSection('stocks')">
            <span class="nav-icon">📋</span>
            <span>종목</span>
        </button>
        <button class="nav-item" onclick="showSection('sectors')">
            <span class="nav-icon">📊</span>
            <span>섹터</span>
        </button>
        <button class="nav-item" onclick="showSection('subsectors')">
            <span class="nav-icon">🔍</span>
            <span>세부</span>
        </button>
    </nav>

    <script>
        function showSection(sectionId) {{
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
            document.getElementById(sectionId).classList.add('active');
            
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.bottom-nav .nav-item').forEach(i => i.classList.remove('active'));
            
            event.target.classList.add('active');
        }}
    </script>
</body>
</html>'''

# Save
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"✅ Portfolio dashboard generated: {OUTPUT_FILE}")
print(f"📊 Total Value: {format_currency(total_value)}")
print(f"📈 Total P&L: {format_currency(abs(total_pnl))} ({total_pnl_pct:+.1f}%)")
print(f"📋 Assets: {len(df_sorted)} (all shown)")