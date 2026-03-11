#!/bin/bash
# KIS Portfolio Daily Update
# 매일 아침 8:50에 실행 (장 시작 10분 전)

export PATH="/usr/local/bin:$PATH"
export HOME="/Users/geon"

# 로그 설정
LOG_FILE="$HOME/.openclaw/workspace/logs/portfolio_update_$(date +%Y%m%d).log"
mkdir -p "$HOME/.openclaw/workspace/logs"

echo "========================================" >> "$LOG_FILE"
echo "🚀 Portfolio Update - $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# 1. KIS API로 주가 수짜 (v3 - KIS API 사용)
echo "📊 Step 1: KIS API 주가 수짜 (v3)" >> "$LOG_FILE"
cd "$HOME/.openclaw/workspace/scripts"
python3 update_prices_v3.py >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    echo "✅ KIS 데이터 수짜 완료" >> "$LOG_FILE"
else
    echo "⚠️ KIS 데이터 수짜 일부 실패 (API 제한 가능)" >> "$LOG_FILE"
fi

echo "" >> "$LOG_FILE"

# 2. HTML 페이지 생성
echo "🎨 Step 2: HTML 페이지 생성" >> "$LOG_FILE"
python3 << 'PYEOF' >> "$LOG_FILE" 2>&1
import sqlite3
import os
from datetime import datetime

# DB 연결
db_path = os.path.expanduser('~/.openclaw/workspace/prices.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 최신 데이터 조회
cursor.execute('SELECT symbol, name, price, change, change_pct, volume FROM prices ORDER BY name')
rows = cursor.fetchall()
conn.close()

if not rows:
    print("❌ 데이터 없음")
    exit(1)

# HTML 생성
html_content = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Geon's Portfolio - KIS API Daily</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0a0e1a;
            color: #e8eaed;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        header {{
            text-align: center;
            padding: 30px 0;
            border-bottom: 2px solid #1a2332;
            margin-bottom: 30px;
        }}
        h1 {{ font-size: 2em; margin-bottom: 10px; }}
        .subtitle {{ color: #8b949e; font-size: 0.9em; }}
        .timestamp {{
            color: #58a6ff;
            font-size: 0.85em;
            margin-top: 10px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background: linear-gradient(135deg, #1a2332 0%, #0d1117 100%);
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #30363d;
        }}
        .summary-card h3 {{
            color: #8b949e;
            font-size: 0.85em;
            margin-bottom: 8px;
        }}
        .summary-card .value {{
            font-size: 1.8em;
            font-weight: bold;
        }}
        .up {{ color: #3fb950; }}
        .down {{ color: #f85149; }}
        .neutral {{ color: #8b949e; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: #0d1117;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid #30363d;
        }}
        th, td {{
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #21262d;
        }}
        th {{
            background: #161b22;
            font-weight: 600;
            color: #8b949e;
            font-size: 0.85em;
            text-transform: uppercase;
        }}
        tr:hover {{ background: #161b22; }}
        .symbol {{ color: #58a6ff; font-family: monospace; }}
        .price {{ font-weight: bold; font-size: 1.1em; }}
        .change {{ font-weight: 600; }}
        .volume {{ color: #8b949e; text-align: right; }}
        footer {{
            text-align: center;
            padding: 30px 0;
            color: #8b949e;
            font-size: 0.85em;
            border-top: 1px solid #21262d;
            margin-top: 30px;
        }}
        .api-badge {{
            display: inline-block;
            background: #238636;
            color: white;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.75em;
            margin-left: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Geon's Portfolio <span class="api-badge">KIS API Daily</span></h1>
            <p class="subtitle">한국투자증권 Open API 연동 포트폴리오</p>
            <p class="timestamp">업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} KST</p>
        </header>

        <div class="summary">
            <div class="summary-card">
                <h3>보유 종목</h3>
                <div class="value neutral">{len(rows)}개</div>
            </div>
            <div class="summary-card">
                <h3>상승 종목</h3>
                <div class="value up">{sum(1 for r in rows if r[4] > 0)}개</div>
            </div>
            <div class="summary-card">
                <h3>하락 종목</h3>
                <div class="value down">{sum(1 for r in rows if r[4] < 0)}개</div>
            </div>
            <div class="summary-card">
                <h3>데이터 소스</h3>
                <div class="value neutral">KIS API ✅</div>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th>종목명</th>
                    <th>종목코드</th>
                    <th style="text-align:right">현재가</th>
                    <th style="text-align:right">전일대비</th>
                    <th style="text-align:right">등락률</th>
                    <th style="text-align:right">거래량</th>
                </tr>
            </thead>
            <tbody>
'''

# 종목 데이터 추가
for row in rows:
    symbol, name, price, change, change_pct, volume = row
    change_class = 'up' if change_pct > 0 else ('down' if change_pct < 0 else 'neutral')
    
    html_content += f'''
                <tr>
                    <td><strong>{name}</strong></td>
                    <td class="symbol">{symbol}</td>
                    <td class="price" style="text-align:right">₩{price:,}</td>
                    <td class="change {change_class}" style="text-align:right">{change:+,}</td>
                    <td class="change {change_class}" style="text-align:right">{change_pct:+.2f}%</td>
                    <td class="volume" style="text-align:right">{volume:,}</td>
                </tr>
'''

html_content += f'''
            </tbody>
        </table>

        <footer>
            <p>📡 데이터 출처: 한국투자증권(KIS) Open API</p>
            <p>🔄 자동 업데이트: 매일 08:50 KST | 생성: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </footer>
    </div>
</body>
</html>
'''

# HTML 파일 저장
output_path = os.path.expanduser('~/.openclaw/workspace/portfolio_kis.html')
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"✅ HTML 생성 완료: {output_path}")
print(f"   종목 수: {len(rows)}개")
PYEOF

if [ $? -eq 0 ]; then
    echo "✅ HTML 페이지 생성 완료" >> "$LOG_FILE"
    echo "📁 파일: $HOME/.openclaw/workspace/portfolio_kis.html" >> "$LOG_FILE"
else
    echo "❌ HTML 생성 실패" >> "$LOG_FILE"
fi

echo "" >> "$LOG_FILE"
echo "✨ 완료 시간: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Telegram 알림 (선택적)
# TELEGRAM_BOT_TOKEN과 CHAT_ID가 설정된 경우에만 실행
if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
    curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
        -d "chat_id=$TELEGRAM_CHAT_ID" \
        -d "text=📊 포트폴리오 업데이트 완료 ($(date '+%H:%M'))\n\n🔍 $HOME/.openclaw/workspace/portfolio_kis.html" > /dev/null
fi

exit 0
