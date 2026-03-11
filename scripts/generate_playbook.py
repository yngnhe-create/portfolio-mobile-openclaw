#!/usr/bin/env python3
"""
Dynamic Playbook Generator - Fixed Version
Handles virtual assets correctly
"""

import pandas as pd
import re
from datetime import datetime

WORKSPACE = "/Users/geon/.openclaw/workspace"
CSV_PATH = f"{WORKSPACE}/portfolio_full.csv"
OUTPUT_PATH = f"{WORKSPACE}/public/portfolio_playbook_live.html"

def parse_currency(value):
    """Parse currency value to number"""
    if pd.isna(value) or value == '-':
        return 0
    s = str(value).replace(',', '').replace('₩', '').replace('$', '').replace('"', '')
    s = re.sub(r'[\(\)]', '', s)
    try:
        return float(s)
    except:
        return 0

def parse_quantity(value):
    """Parse quantity"""
    if pd.isna(value):
        return 0
    try:
        return float(str(value).replace(',', ''))
    except:
        return 0

def parse_return(value):
    """Parse return percentage"""
    if pd.isna(value):
        return 0
    s = str(value).replace(',', '')
    match = re.search(r'([+-]?[\d.]+)%', s)
    if match:
        return float(match.group(1))
    return 0

def parse_pnl_amount(value):
    """Parse P&L amount (수익금액) from string like '+₩77,433,243 (+221.68%)'"""
    if pd.isna(value) or value == '-':
        return 0
    s = str(value).replace(',', '').replace('"', '')
    # Extract the amount before parentheses
    match = re.search(r'([+-]?[₩$]?[\d,]+)', s)
    if match:
        amount_str = match.group(1).replace('₩', '').replace('$', '').replace(',', '')
        try:
            # Check if negative
            if '(-' in s or amount_str.startswith('-'):
                return -abs(float(amount_str.replace('-', '')))
            return float(amount_str)
        except:
            return 0
    return 0

def format_currency(value, currency='₩'):
    """Format currency with appropriate unit"""
    if value >= 100000000:
        return f"{currency}{value/100000000:.1f}억"
    elif value >= 10000000:
        return f"{currency}{value/10000000:.0f}천만"
    elif value >= 1000000:
        return f"{currency}{value/1000000:.0f}백만"
    else:
        return f"{currency}{value:,.0f}"

def generate_playbook():
    """Generate playbook from portfolio data"""
    
    df = pd.read_csv(CSV_PATH)
    
    # Parse data
    df['수익률_숫자'] = df['손익'].apply(parse_return)
    df['수익금액_숫자'] = df['손익'].apply(parse_pnl_amount)  # 수익금액 추가
    df['자산가치_숫자'] = df['자산가치'].apply(parse_currency)
    df['수량_숫자'] = df['수량'].apply(parse_quantity)
    df['매수가_숫자'] = df['매수가'].apply(parse_currency)
    df['현재가_숫자'] = df['현재가'].apply(parse_currency)
    
    # Calculate unit price for virtual assets
    def get_display_price(row):
        """Get proper unit price for display"""
        asset_name = str(row['자산'])
        qty = row['수량_숫자']
        current = row['현재가_숫자']
        value = row['자산가치_숫자']
        
        # For virtual assets, calculate unit price
        if 'BTC' in asset_name or 'ETH' in asset_name or '가상자산' in str(row['분류']):
            if qty > 0:
                unit_price = value / qty  # Use total value / quantity
                return unit_price, value, f"{format_currency(unit_price)} × {qty}개"
        
        # For stocks, use as-is
        return current, value, format_currency(current)
    
    df['단가_표시'], df['총액_표시'], df['가격_표시'] = zip(*df.apply(get_display_price, axis=1))
    
    # Calculate totals
    total_value = df['자산가치_숫자'].sum()
    total_pnl = df['손익'].apply(lambda x: parse_currency(str(x).split('(')[0]) if pd.notna(x) else 0).sum()
    total_return = (total_pnl / (total_value - total_pnl) * 100) if (total_value - total_pnl) > 0 else 0
    
    # Top gainers/losers by P&L amount (수익금액 기준)
    top_gainers = df.nlargest(3, '수익금액_숫자')[['자산', '수익률_숫자', '수익금액_숫자', '분류', '가격_표시', '수량_숫자']]
    top_losers = df.nsmallest(3, '수익금액_숫자')[['자산', '수익률_숫자', '수익금액_숫자', '분류', '가격_표시', '수량_숫자']]
    
    # Sector breakdown
    sector_data = df.groupby('분류')['자산가치_숫자'].sum().sort_values(ascending=False)
    sector_pct = (sector_data / total_value * 100).round(1)
    
    now = datetime.now().strftime('%Y년 %m월 %d일 %H:%M')
    
    # Generate HTML components
    gainers_html = ""
    for _, row in top_gainers.iterrows():
        gainers_html += f'''
                <div style="font-size: 0.875rem; margin-bottom: 6px; padding: 8px; background: rgba(16, 185, 129, 0.1); border-radius: 8px;">
                    <div style="font-weight: 600;">{row['자산']}</div>
                    <div style="font-size: 0.75rem; color: #94a3b8;">{row['가격_표시']} ({row['분류']})</div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px;">
                        <span class="positive" style="font-weight: 700;">+{row['수익률_숫자']:.1f}%</span>
                        <span class="positive" style="font-size: 0.9rem; font-weight: 700;">+{format_currency(row['수익금액_숫자'])}</span>
                    </div>
                </div>'''
    
    losers_html = ""
    for _, row in top_losers.iterrows():
        color = "positive" if row['수익률_숫자'] >= 0 else "negative"
        sign = "+" if row['수익률_숫자'] >= 0 else ""
        pnl_sign = "+" if row['수익금액_숫자'] >= 0 else ""
        losers_html += f'''
                <div style="font-size: 0.875rem; margin-bottom: 6px; padding: 8px; background: rgba(248, 81, 73, 0.1); border-radius: 8px;">
                    <div style="font-weight: 600;">{row['자산']}</div>
                    <div style="font-size: 0.75rem; color: #94a3b8;">{row['가격_표시']} ({row['분류']})</div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px;">
                        <span class="{color}" style="font-weight: 700;">{sign}{row['수익률_숫자']:.1f}%</span>
                        <span class="{color}" style="font-size: 0.9rem; font-weight: 700;">{pnl_sign}{format_currency(row['수익금액_숫자'])}</span>
                    </div>
                </div>'''
    
    sector_html = ""
    for sector, pct in sector_pct.head(6).items():
        sector_value = sector_data[sector]
        sector_html += f'''
            <div class="metric-row" style="padding: 8px 0; border-bottom: 1px solid var(--border-color);">
                <span class="metric-label">{sector}</span>
                <div style="text-align: right;">
                    <div class="metric-value">{pct}%</div>
                    <div style="font-size: 0.7rem; color: #64748b;">{format_currency(sector_value)}</div>
                </div>
            </div>'''
    
    # Create full HTML
    html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 포트폴리오 운영 플레이북</title>
    <style>
        :root {{
            --bg-primary: #0a0e14;
            --bg-secondary: #111820;
            --bg-card: #1a2332;
            --accent-blue: #58a6ff;
            --accent-green: #3fb950;
            --accent-red: #f85149;
            --accent-yellow: #d29922;
            --text-primary: #f0f6fc;
            --text-secondary: #8b949e;
            --border-color: #30363d;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.5;
            padding-bottom: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #1d4ed8, #7c3aed);
            padding: 20px 16px;
        }}
        .header-title {{ font-size: 1.3rem; font-weight: 700; }}
        .update-time {{ font-size: 0.75rem; opacity: 0.85; margin-top: 8px; }}
        .container {{ padding: 16px; max-width: 600px; margin: 0 auto; }}
        
        .card {{
            background: var(--bg-card);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            border: 1px solid var(--border-color);
        }}
        .card-title {{
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--border-color);
        }}
        
        .metric-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}
        .metric-label {{ color: var(--text-secondary); font-size: 0.875rem; }}
        .metric-value {{ font-weight: 600; }}
        .positive {{ color: var(--accent-green); }}
        .negative {{ color: var(--accent-red); }}
        .warning {{ color: var(--accent-yellow); }}
        
        .action-item {{
            background: var(--bg-secondary);
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 10px;
            border-left: 3px solid var(--accent-blue);
        }}
        .action-item.high {{ border-left-color: var(--accent-red); }}
        .action-item.medium {{ border-left-color: var(--accent-yellow); }}
        
        .action-header {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 6px;
        }}
        .action-icon {{ font-size: 1.2rem; }}
        .action-title {{ font-weight: 600; font-size: 0.9rem; }}
        .action-desc {{ font-size: 0.8rem; color: var(--text-secondary); line-height: 1.4; }}
        
        .priority-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.7rem;
            font-weight: 600;
            margin-left: auto;
        }}
        .priority-high {{ background: rgba(248, 81, 73, 0.2); color: var(--accent-red); }}
        .priority-medium {{ background: rgba(210, 153, 34, 0.2); color: var(--accent-yellow); }}
        
        .section-title {{
            font-size: 1.1rem;
            font-weight: 700;
            margin: 24px 0 12px;
            color: var(--accent-blue);
        }}
        
        .wisererport-box {{
            background: linear-gradient(135deg, rgba(29, 155, 240, 0.1), rgba(139, 92, 246, 0.1));
            border: 1px solid var(--accent-blue);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 16px;
        }}
        .wisererport-title {{
            font-weight: 700;
            color: var(--accent-blue);
            margin-bottom: 8px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-title">📊 포트폴리오 운영 플레이북</div>
        <div class="update-time">⏱️ {now} KST 기준 (자동 생성)</div>
    </div>
    
    <div class="container">
        <!-- WiseReport Integration -->
        <div class="wisererport-box">
            <div class="wisererport-title">📈 오늘의 WiseReport 연동</div>
            <div style="font-size: 0.875rem; margin-bottom: 8px;">
                <b>추천 종목:</b> 씨젠, 피에스케이홀딩스, 포스코퓨처엠
            </div>
            <div style="font-size: 0.8rem; color: var(--text-secondary);">
                • 씨젠 +63%, 피에스케이홀딩스 +55%, 포스코퓨처엠 +50% 상승여력
            </div>
        </div>
        
        <!-- Portfolio Summary -->
        <div class="card">
            <div class="card-title">💼 포트폴리오 현황</div>
            <div class="metric-row">
                <span class="metric-label">총 자산</span>
                <span class="metric-value" style="font-size: 1.2rem;">{format_currency(total_value)}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">총 손익</span>
                <span class="metric-value {'positive' if total_pnl >= 0 else 'negative'}" style="font-size: 1.1rem;">
                    {'+' if total_pnl >= 0 else ''}{format_currency(abs(total_pnl))} ({'+' if total_return >= 0 else ''}{total_return:.1f}%)
                </span>
            </div>
            <div class="metric-row" style="margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border-color);">
                <span class="metric-label" style="font-size: 0.75rem;">보유 종목 수</span>
                <span class="metric-value" style="font-size: 0.875rem;">{len(df)}개</span>
            </div>
        </div>
        
        <!-- Sector Breakdown -->
        <div class="card">
            <div class="card-title">🏭 섹터별 비중</div>
            {sector_html}
        </div>
        
        <!-- Top Gainers/Losers by P&L Amount -->
        <div class="card">
            <div class="card-title">📊 수익금액 TOP 3 / BOTTOM 3</div>
            <div style="margin-bottom: 16px;">
                <div style="font-size: 0.85rem; color: var(--accent-green); margin-bottom: 10px; font-weight: 600;">🔼 최고 수익</div>
                {gainers_html}
            </div>
            <div>
                <div style="font-size: 0.85rem; color: var(--accent-red); margin-bottom: 10px; font-weight: 600;">🔽 최대 손실</div>
                {losers_html}
            </div>
        </div>
        
        <!-- Action Items -->
        <div class="section-title">🎯 권장 액션</div>

        <div class="action-item high">
            <div class="action-header">
                <span class="action-icon">📊</span>
                <span class="action-title">WiseReport 추천 종목 관심</span>
                <span class="priority-badge priority-high">HIGH</span>
            </div>
            <div class="action-desc">씨젠 +63%, 피에스케이홀딩스 +55%, 포스코퓨처엠 +50% 상승여력</div>
        </div>
        
        <div class="action-item high">
            <div class="action-header">
                <span class="action-icon">🎯</span>
                <span class="action-title">고수익 종목 점검 필요</span>
                <span class="priority-badge priority-high">HIGH</span>
            </div>
            <div class="action-desc">세아베스틸지주 +453%, 삼성전자우 +212% 등 목표 수익률 도달 종목 수익 실현 검토</div>
        </div>
        
        <div class="action-item medium">
            <div class="action-header">
                <span class="action-icon">⚠️</span>
                <span class="action-title">첨단 기술 섹터 과중 집중</span>
                <span class="priority-badge priority-medium">MEDIUM</span>
            </div>
            <div class="action-desc">반도체/AI 비중 확인 및 분산 투자 고려</div>
        </div>
        
        <div style="text-align: center; padding: 20px; color: var(--text-secondary); font-size: 0.75rem;">
            📊 포트폴리오 CSV 자동 연동 | 생성: {now}
        </div>
    </div>
</body>
</html>'''
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Playbook generated: {OUTPUT_PATH}")
    print(f"📊 Total value: {format_currency(total_value)}")
    print(f"💰 Total P&L: {'+' if total_pnl >= 0 else ''}{format_currency(abs(total_pnl))}")
    print(f"📈 Total return: {'+' if total_return >= 0 else ''}{total_return:.1f}%")
    print(f"📋 Assets count: {len(df)}")
    print("\n🔝 Top 3 gainers:")
    for _, row in top_gainers.iterrows():
        print(f"  • {row['자산']}: +{row['수익률_숫자']:.1f}% ({row['가격_표시']})")
    print("\n🔻 Top 3 losers:")
    for _, row in top_losers.iterrows():
        sign = "+" if row['수익률_숫자'] >= 0 else ""
        print(f"  • {row['자산']}: {sign}{row['수익률_숫자']:.1f}% ({row['가격_표시']})")

if __name__ == "__main__":
    generate_playbook()