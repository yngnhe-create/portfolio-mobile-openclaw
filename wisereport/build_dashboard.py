#!/usr/bin/env python3
"""Generate mobile-friendly WiseReport HTML page"""
from pathlib import Path
from datetime import datetime

BASE = Path('/Users/geon/.openclaw/workspace')
MEMORY = BASE / 'memory'
PUBLIC = BASE / 'public'

# Get today's date
TODAY = datetime.now().strftime('%Y-%m-%d')
auto_file = MEMORY / f'{TODAY}-wisereport-summary.md'

if not auto_file.exists():
    print(f"❌ No summary found for {TODAY}")
    # Try to find the most recent file
    files = sorted(MEMORY.glob('*wisereport-summary.md'), reverse=True)
    if files:
        auto_file = files[0]
        print(f"📁 Using most recent file: {auto_file.name}")
    else:
        exit(1)

# Parse content
content = auto_file.read_text(encoding='utf-8')

# Parse sections
lines = content.split('\n')
data = {
    'date': TODAY,
    'today_reports': [],
    'sectors': {},
    'buy_by_sector': {},
    'hot_news': []
}

current_section = None
import re
for i, line in enumerate(lines):
    stripped = line.strip()

    # Today reports
    if 'Today Top Report' in stripped or 'Today Hot Report' in stripped or 'Today Best Report' in stripped:
        report_type = 'Top' if 'Top' in stripped else 'Hot' if 'Hot' in stripped else 'Best'

        # Extract name and ticker from the same line (e.g., "Today Top Report - 한국전력 (015760)")
        match = re.search(r'Today (?:Top|Hot|Best) Report - (.+?) \((\d+)\)', stripped)
        if match:
            name = match.group(1)
            ticker = match.group(2)
        else:
            # Try alternative format
            match = re.search(r'(.+?) \((\d+)\)', stripped)
            if match:
                name = match.group(1)
                ticker = match.group(2)
            else:
                continue

        # Get the next 4 lines (dashed line, opinion, target, title)
        next_lines = lines[i+1:i+5]
        report = {
            'type': report_type,
            'name': name.strip(),
            'ticker': ticker
        }
        for nl in next_lines:
            nl = nl.strip()
            if '투자의견:' in nl:
                report['opinion'] = nl.split('투자의견:')[1].strip()
            elif '목표가:' in nl:
                report['target'] = nl.split('목표가:')[1].strip()
            elif '제목:' in nl:
                report['title'] = nl.split('제목:')[1].strip()

        data['today_reports'].append(report)

    # Sectors table
    elif '전체 리포트' in stripped:
        # Find table start
        table_start = i
        for j in range(i, min(i+30, len(lines))):
            if '|' in lines[j] and '---' not in lines[j]:
                table_start = j
                break

        # Parse table rows until empty line or BUY section
        for j in range(table_start, min(table_start+20, len(lines))):
            row = lines[j].strip()
            if not row or 'BUY 권장' in row:
                break
            if '|' not in row or '---' in row or '섹터' in row:
                continue
            cells = [c.strip() for c in row.split('|')[1:-1]]
            if len(cells) >= 2:
                sector = cells[0]
                count = cells[1].replace(',', '').replace('개', '').strip()
                if sector and count and count.isdigit():
                    data['sectors'][sector] = int(count)

    # BUY by sector
    elif 'BUY 권장' in stripped and any('BUY 수' in l for l in lines[i:i+5]):
        # Find the table header with "BUY 수"
        table_start = None
        for j in range(i, min(i+30, len(lines))):
            if '|' in lines[j] and 'BUY 수' in lines[j]:
                table_start = j + 1
                break
        
        if table_start:
            # Parse table rows
            for j in range(table_start, min(table_start+20, len(lines))):
                row = lines[j]
                if '|' not in row or '---' in row or '섹터' in row or 'BUY 수' in row:
                    continue
                cells = [c.strip() for c in row.split('|')[1:-1]]
                if len(cells) >= 2:
                    sector = cells[0]
                    count = cells[1].replace(',', '').replace('개', '').strip()
                    if sector and count and count.isdigit():
                        data['buy_by_sector'][sector] = int(count)

    # Hot news
    elif 'Hot 뉴스' in stripped:
        news_count = 0
        for j in range(i+1, min(i+20, len(lines))):
            nl = lines[j].strip()
            # Only break if we've collected at least one news item and hit a separator
            if nl.startswith('---') or nl.startswith('**기준일'):
                break
            # Don't break on empty lines until we've collected news
            if not nl and news_count > 0:
                continue
            if not nl:
                continue
            # Extract news title (e.g., "1. **미국 기술주 부진 속 외국인 4조원 투매** - 26/02/27")
            if re.match(r'^\d+\.', nl):
                news_count += 1
                # Remove the number prefix
                news_text = re.sub(r'^\d+\.\s*', '', nl)
                # Extract title (between ** and **)
                title_match = re.search(r'\*\*(.+?)\*\*', news_text)
                if title_match:
                    title = title_match.group(1)
                    # Extract source/date (after ** and -)
                    source = ''
                    source_match = re.search(r'[-–]\s*(.+)$', news_text)
                    if source_match:
                        source = source_match.group(1).strip()
                    data['hot_news'].append({'title': title, 'source': source})

# Build HTML
html = f'''<!doctype html>
<html lang="ko">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>와이즈리포트 요약</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ margin:0; background:#0f1419; color:#e7e9ea; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; line-height:1.6; }}
        .wrap {{ padding:16px; max-width:600px; margin:0 auto }}
        h1 {{ color:#1d9bf0; font-size:22px; margin:0 0 4px }}
        .date {{ color:#71767b; font-size:13px; margin-bottom:20px }}
        h2 {{ color:#fff; font-size:18px; margin:24px 0 12px; border-bottom:2px solid #2f3336; padding-bottom:8px }}
        .card {{ background:#15202b; border-radius:12px; padding:16px; margin-bottom:12px }}
        .section {{ margin-bottom:24px }}

        /* Today reports */
        .report-item {{ margin:12px 0; padding:12px; background:#1e2d3d; border-radius:8px; border-left:4px solid #1d9bf0 }}
        .report-badge {{ display:inline-block; padding:4px 8px; border-radius:4px; font-size:11px; font-weight:700; margin-bottom:6px }}
        .report-top {{ background:#ffd400; color:#000 }}
        .report-hot {{ background:#f4212e; color:#fff }}
        .report-best {{ background:#00ba7c; color:#fff }}
        .report-name {{ font-size:16px; font-weight:700; color:#fff; margin:4px 0 }}
        .report-title {{ font-size:13px; color:#71767b; margin:4px 0 }}
        .report-meta {{ font-size:12px; color:#71767b; display:flex; gap:12px }}
        .meta-item {{ display:flex; align-items:center; gap:4px }}
        .opinion-buy {{ color:#00ba7c; font-weight:600 }}
        .opinion-hold {{ color:#ffd400; font-weight:600 }}

        /* Stats */
        .stats {{ display:flex; gap:12px; margin:20px 0 }}
        .stat {{ flex:1; text-align:center; padding:16px 12px; background:#15202b; border-radius:12px }}
        .stat-num {{ font-size:28px; font-weight:700; color:#1d9bf0 }}
        .stat-label {{ font-size:12px; color:#71767b; margin-top:4px }}

        /* Tables */
        table {{ width:100%; border-collapse:collapse; font-size:13px; margin:12px 0 }}
        th {{ padding:10px 8px; text-align:left; background:#1e2d3d; color:#71767b; font-weight:600; font-size:11px }}
        td {{ padding:10px 8px; border-bottom:1px solid #2f3336 }}
        .sector-row:hover {{ background:#1d3a5f }}
        .count {{ font-weight:600; text-align:right }}
        .bar-bg {{ height:6px; background:#2f3336; border-radius:3px; margin:4px 0; overflow:hidden }}
        .bar-fill {{ height:100%; background:#1d9bf0; border-radius:3px; transition:width 0.3s }}
        .buy-bar {{ background:#00ba7c }}

        /* News */
        .news-item {{ padding:12px 0; border-bottom:1px solid #2f3336 }}
        .news-item:last-child {{ border-bottom:none }}
        .news-title {{ font-size:14px; font-weight:500; margin:4px 0 }}
        .news-meta {{ font-size:11px; color:#71767b }}
        .news-num {{ display:inline-block; width:20px; height:20px; background:#1d9bf0; color:#fff; border-radius:50%; text-align:center; line-height:20px; font-size:11px; margin-right:8px }}

        .badge {{ background:#1d9bf0; color:#fff; padding:2px 6px; border-radius:4px; font-size:11px }}
        .buy-badge {{ background:#00ba7c }}
    </style>
</head>
<body>
    <div class="wrap">
        <h1>📊 와이즈리포트</h1>
        <div class="date">{TODAY} 기준</div>

        <!-- Stats -->
        <div class="stats">
            <div class="stat">
                <div class="stat-num">{sum(data['sectors'].values())}</div>
                <div class="stat-label">전체 리포트</div>
            </div>
            <div class="stat">
                <div class="stat-num">{sum(data['buy_by_sector'].values())}</div>
                <div class="stat-label">BUY 권장</div>
            </div>
            <div class="stat">
                <div class="stat-num">{len(data['sectors'])}</div>
                <div class="stat-label">섹터 수</div>
            </div>
        </div>

        <!-- Today Reports -->
        <div class="section">
            <h2>🔥 Today 리포트</h2>
            <div class="card">
'''

for report in data['today_reports']:
    badge_class = f"report-{report['type'].lower()}"
    html += f'''
                <div class="report-item">
                    <span class="report-badge {badge_class}">Today {report['type']}</span>
                    <div class="report-name">{report.get('name', '')} {report.get('ticker', '')}</div>
                    <div class="report-title">{report.get('title', '')}</div>
                    <div class="report-meta">
                        <div class="meta-item">
                            <span>투자의견:</span>
                            <span class="{'opinion-buy' if 'BUY' in report.get('opinion', '') or '매수' in report.get('opinion', '') else 'opinion-hold'}">{report.get('opinion', '')}</span>
                        </div>
                        <div class="meta-item">
                            <span>목표가:</span>
                            <span>{report.get('target', '')}</span>
                        </div>
                    </div>
                </div>
'''

# Sectors table
sectors_sorted = sorted(data['sectors'].items(), key=lambda x: x[1], reverse=True)
max_count = max(data['sectors'].values()) if data['sectors'] else 1

html += '''
            </div>
        </div>

        <!-- Sectors -->
        <div class="section">
            <h2>📈 섹터별 리포트</h2>
            <div class="card">
                <table>
                    <tr>
                        <th>섹터</th>
                        <th style="text-align:right">리포트 수</th>
                    </tr>
'''

for sector, count in sectors_sorted:
    bar_width = (count / max_count) * 100
    html += f'''
                    <tr class="sector-row">
                        <td>
                            <div style="font-weight:600">{sector}</div>
                            <div class="bar-bg">
                                <div class="bar-fill" style="width:{bar_width}%"></div>
                            </div>
                        </td>
                        <td class="count">{count}</td>
                    </tr>
'''

# BUY by sector
buy_sorted = sorted(data['buy_by_sector'].items(), key=lambda x: x[1], reverse=True)
max_buy = max(data['buy_by_sector'].values()) if data['buy_by_sector'] else 1

html += '''
                </table>
            </div>
        </div>

        <!-- BUY by Sector -->
        <div class="section">
            <h2>📊 BUY 권장 섹터</h2>
            <div class="card">
                <table>
                    <tr>
                        <th>섹터</th>
                        <th style="text-align:right">BUY 수</th>
                    </tr>
'''

for sector, count in buy_sorted:
    bar_width = (count / max_buy) * 100
    html += f'''
                    <tr class="sector-row">
                        <td>
                            <div style="font-weight:600">{sector}</div>
                            <div class="bar-bg">
                                <div class="bar-fill buy-bar" style="width:{bar_width}%"></div>
                            </div>
                        </td>
                        <td class="count"><span class="buy-badge">{count}</span></td>
                    </tr>
'''

# Hot news
html += '''
                </table>
            </div>
        </div>

        <!-- Hot News -->
        <div class="section">
            <h2>📰 Hot 뉴스</h2>
            <div class="card">
'''

for idx, news in enumerate(data['hot_news'], 1):
    html += f'''
                <div class="news-item">
                    <div class="news-title"><span class="news-num">{idx}</span>{news['title']}</div>
                    <div class="news-meta">{news['source']}</div>
                </div>
'''

html += '''
            </div>
        </div>
    </div>
</body>
</html>'''

# Save
out_file = PUBLIC / 'wisereport_summary.html'
out_file.write_text(html, encoding='utf-8')

print(f'✅ 와이즈리포트 대시보드 현행화 완료')
print(f'📁 저장 위치: {out_file}')
print(f'📊 기준일: {TODAY}')
print(f'   - 전체 리포트: {sum(data["sectors"].values())}개')
print(f'   - BUY 권장: {sum(data["buy_by_sector"].values())}개')
print(f'   - Today 리포트: {len(data["today_reports"])}개')
print(f'   - Hot 뉴스: {len(data["hot_news"])}개')
